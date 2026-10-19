import re
import threading
from pathlib import Path
from typing import Optional

from grep_ast import TreeContext
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from watchfiles import watch

from aider.dump import dump  # noqa
from aider.watch_prompts import watch_ask_prompt, watch_code_prompt


def load_gitignores(gitignore_paths: list[Path]) -> Optional[PathSpec]:
    """Carrega e processa vários arquivos .gitignore em um único PathSpec"""
    if not gitignore_paths:
        return None

    patterns = [
        ".aider*",
        ".git",
        # Arquivos comuns de backup/temporários de editores
        "*~",  # Backup do Emacs/vim
        "*.bak",  # Backup genérico
        "*.swp",  # Swap do Vim
        "*.swo",  # Swap do Vim
        "\\#*\\#",  # Salvamento automático do Emacs
        ".#*",  # Arquivos de bloqueio do Emacs
        "*.tmp",  # Arquivos temporários genéricos
        "*.temp",  # Arquivos temporários genéricos
        "*.orig",  # Originais de conflitos de merge
        "*.pyc",  # Bytecode do Python
        "__pycache__/",  # Diretório de cache do Python
        ".DS_Store",  # Metadados do macOS
        "Thumbs.db",  # Cache de miniaturas do Windows
        "*.svg",
        "*.pdf",
        # Arquivos de IDE
        ".idea/",  # IDEs JetBrains
        ".vscode/",  # VS Code
        "*.sublime-*",  # Sublime Text
        ".project",  # Eclipse
        ".settings/",  # Eclipse
        "*.code-workspace",  # Workspace do VS Code
        # Arquivos de ambiente
        ".env",  # Variáveis de ambiente
        ".venv/",  # Ambientes virtuais Python
        "node_modules/",  # Dependências do Node.js
        "vendor/",  # Dependências diversas
        # Logs e caches
        "*.log",  # Arquivos de log
        ".cache/",  # Diretórios de cache
        ".pytest_cache/",  # Cache de testes do Python
        "coverage/",  # Relatórios de cobertura de código
    ]  # Sempre ignorar
    for path in gitignore_paths:
        if path.exists():
            with open(path) as f:
                patterns.extend(f.readlines())

    return PathSpec.from_lines(GitWildMatchPattern, patterns) if patterns else None


class FileWatcher:
    """Monitora arquivos-fonte em busca de alterações e comentários de IA"""

    # Padrão regex compilado para comentários de IA
    ai_comment_pattern = re.compile(
        r"(?:#|//|--|;+) *(ai\b.*|ai\b.*|.*\bai[?!]?) *$", re.IGNORECASE
    )

    def __init__(self, coder, gitignores=None, verbose=False, analytics=None, root=None):
        self.coder = coder
        self.io = coder.io
        self.root = Path(root) if root else Path(coder.root)
        self.verbose = verbose
        self.analytics = analytics
        self.stop_event = None
        self.watcher_thread = None
        self.changed_files = set()
        self.gitignores = gitignores

        self.gitignore_spec = load_gitignores(
            [Path(g) for g in self.gitignores] if self.gitignores else []
        )

        coder.io.file_watcher = self

    def filter_func(self, change_type, path):
        """Função de filtro para o monitor de arquivos"""
        path_obj = Path(path)
        path_abs = path_obj.absolute()

        if not path_abs.is_relative_to(self.root.absolute()):
            return False

        rel_path = path_abs.relative_to(self.root)
        if self.verbose:
            print("Alterado", rel_path)

        if self.gitignore_spec and self.gitignore_spec.match_file(
            rel_path.as_posix() + ("/" if path_abs.is_dir() else "")
        ):
            return False

        # Verifica o tamanho do arquivo antes de ler o conteúdo
        if path_abs.is_file() and path_abs.stat().st_size > 1 * 1024 * 1024:  # limite de 1 MB
            return False

        if self.verbose:
            print("Verificando", rel_path)

        # Verifica se o arquivo contém marcadores de IA
        try:
            comments, _, _ = self.get_ai_comments(str(path_abs))
            return bool(comments)
        except Exception:
            return

    def get_roots_to_watch(self):
        """Determina quais caminhos raiz monitorar com base nas regras do gitignore"""
        if self.gitignore_spec:
            roots = [
                str(path)
                for path in self.root.iterdir()
                if not self.gitignore_spec.match_file(
                    path.relative_to(self.root).as_posix() + ("/" if path.is_dir() else "")
                )
            ]
            # Se todos os itens de nível superior forem filtrados, monitora a raiz
            return roots if roots else [str(self.root)]
        return [str(self.root)]

    def handle_changes(self, changes):
        """Processa as alterações detectadas e atualiza o estado"""
        if not changes:
            return False

        changed_files = {str(Path(change[1])) for change in changes}
        self.changed_files.update(changed_files)
        self.io.interrupt_input()
        return True

    def watch_files(self):
        """Monitora alterações em arquivos e as processa"""
        try:
            roots_to_watch = self.get_roots_to_watch()

            for changes in watch(
                *roots_to_watch,
                watch_filter=self.filter_func,
                stop_event=self.stop_event,
                ignore_permission_denied=True,
            ):
                if self.handle_changes(changes):
                    return

        except Exception as e:
            if self.verbose:
                dump(f"Erro no monitor de arquivos: {e}")
            raise e

    def start(self):
        """Inicia o monitoramento de alterações em arquivos"""
        self.stop_event = threading.Event()
        self.changed_files = set()

        self.watcher_thread = threading.Thread(target=self.watch_files, daemon=True)
        self.watcher_thread.start()

    def stop(self):
        """Interrompe o monitoramento de alterações em arquivos"""
        if self.stop_event:
            self.stop_event.set()
        if self.watcher_thread:
            self.watcher_thread.join()
            self.watcher_thread = None
            self.stop_event = None

    def process_changes(self):
        """Obtém quaisquer alterações de arquivo detectadas"""

        has_action = None
        added = False
        for fname in self.changed_files:
            _, _, action = self.get_ai_comments(fname)
            if action in ("!", "?"):
                has_action = action

            if fname in self.coder.abs_fnames:
                continue
            if self.analytics:
                self.analytics.event("ai-comments file-add")
            self.coder.abs_fnames.add(fname)
            rel_fname = self.coder.get_rel_fname(fname)
            if not added:
                self.io.tool_output()
                added = True
            self.io.tool_output(f"Adicionado {rel_fname} ao chat")

        if not has_action:
            if added:
                self.io.tool_output(
                    "Termine seu comentário com AI! para solicitar alterações ou AI? para fazer perguntas"
                )
            return ""

        if self.analytics:
            self.analytics.event("ai-comments execute")
        self.io.tool_output("Processando sua solicitação...")

        if has_action == "!":
            res = watch_code_prompt
        elif has_action == "?":
            res = watch_ask_prompt

        # Atualiza todos os comentários de IA dos arquivos rastreados
        for fname in self.coder.abs_fnames:
            line_nums, comments, _action = self.get_ai_comments(fname)
            if not line_nums:
                continue

            code = self.io.read_text(fname)
            if not code:
                continue

            rel_fname = self.coder.get_rel_fname(fname)
            res += f"\n{rel_fname}:\n"

            # Converte números de linha dos comentários em índices de linha (base 0)
            lois = [ln - 1 for ln, _ in zip(line_nums, comments) if ln > 0]

            try:
                context = TreeContext(
                    rel_fname,
                    code,
                    color=False,
                    line_number=False,
                    child_context=False,
                    last_line=False,
                    margin=0,
                    mark_lois=True,
                    loi_pad=3,
                    show_top_of_file_parent_scope=False,
                )
                context.lines_of_interest = set()
                context.add_lines_of_interest(lois)
                context.add_context()
                res += context.format()
            except ValueError:
                for ln, comment in zip(line_nums, comments):
                    res += f"  Linha {ln}: {comment}\n"

        return res

    def get_ai_comments(self, filepath):
        """Extrai números de linha, comentários de IA e o estado da ação de um arquivo"""
        line_nums = []
        comments = []
        has_action = None  # None, "!" ou "?"
        content = self.io.read_text(filepath, silent=True)
        if not content:
            return None, None, None

        for i, line in enumerate(content.splitlines(), 1):
            if match := self.ai_comment_pattern.search(line):
                comment = match.group(0).strip()
                if comment:
                    line_nums.append(i)
                    comments.append(comment)
                    comment = comment.lower()
                    comment = comment.lstrip("/#-;")  # Adicionado ponto e vírgula para comentários Lisp
                    comment = comment.strip()
                    if comment.startswith("ai!") or comment.endswith("ai!"):
                        has_action = "!"
                    elif comment.startswith("ai?") or comment.endswith("ai?"):
                        has_action = "?"
        if not line_nums:
            return None, None, None
        return line_nums, comments, has_action


def main():
    """Exemplo de uso do monitor de arquivos"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitora arquivos-fonte em busca de alterações")
    parser.add_argument("directory", help="Diretório a monitorar")
    parser.add_argument(
        "--gitignore",
        action="append",
        help="Caminho para o arquivo .gitignore (pode ser especificado várias vezes)",
    )
    args = parser.parse_args()

    directory = args.directory
    print(f"Monitorando arquivos-fonte em {directory}...")

    # Exemplo de função que ignora arquivos com "test" no nome
    def ignore_test_files(path):
        return "test" in path.name.lower()

    watcher = FileWatcher(directory, gitignores=args.gitignore)
    try:
        watcher.start()
        while True:
            if changes := watcher.get_changes():
                for file in sorted(changes.keys()):
                    print(file)
                watcher.changed_files = None
    except KeyboardInterrupt:
        print("\nMonitoramento de arquivos interrompido")
        watcher.stop()


if __name__ == "__main__":
    main()
