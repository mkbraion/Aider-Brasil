import os
import re
import subprocess
import sys
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path

import oslex
from grep_ast import TreeContext, filename_to_lang
from grep_ast.tsl import get_parser  # noqa: E402

from aider.dump import dump  # noqa: F401
from aider.run_cmd import run_cmd_subprocess  # noqa: F401

# tree_sitter está emitindo um FutureWarning
warnings.simplefilter("ignore", category=FutureWarning)


class Linter:
    def __init__(self, encoding="utf-8", root=None):
        self.encoding = encoding
        self.root = root

        self.languages = dict(
            python=self.py_lint,
        )
        self.all_lint_cmd = None

    def set_linter(self, lang, cmd):
        if lang:
            self.languages[lang] = cmd
            return

        self.all_lint_cmd = cmd

    def get_rel_fname(self, fname):
        if self.root:
            try:
                return os.path.relpath(fname, self.root)
            except ValueError:
                return fname
        else:
            return fname

    def run_cmd(self, cmd, rel_fname, code):
        cmd += " " + oslex.quote(rel_fname)

        returncode = 0
        stdout = ""
        try:
            returncode, stdout = run_cmd_subprocess(
                cmd,
                cwd=self.root,
                encoding=self.encoding,
            )
        except OSError as err:
            print(f"Não foi possível executar o comando de lint: {err}")
            return
        errors = stdout
        if returncode == 0:
            return  # código de saída zero

        res = f"## Executando: {cmd}\n\n"
        res += errors

        return self.errors_to_lint_result(rel_fname, res)

    def errors_to_lint_result(self, rel_fname, errors):
        if not errors:
            return

        linenums = []
        filenames_linenums = find_filenames_and_linenums(errors, [rel_fname])
        if filenames_linenums:
            filename, linenums = next(iter(filenames_linenums.items()))
            linenums = [num - 1 for num in linenums]

        return LintResult(text=errors, lines=linenums)

    def lint(self, fname, cmd=None):
        rel_fname = self.get_rel_fname(fname)
        try:
            code = Path(fname).read_text(encoding=self.encoding, errors="replace")
        except OSError as err:
            print(f"Não foi possível ler {fname}: {err}")
            return

        if cmd:
            cmd = cmd.strip()
        if not cmd:
            lang = filename_to_lang(fname)
            if not lang:
                return
            if self.all_lint_cmd:
                cmd = self.all_lint_cmd
            else:
                cmd = self.languages.get(lang)

        if callable(cmd):
            lintres = cmd(fname, rel_fname, code)
        elif cmd:
            lintres = self.run_cmd(cmd, rel_fname, code)
        else:
            lintres = basic_lint(rel_fname, code)

        if not lintres:
            return

        res = "# Corrija os erros abaixo, se possível.\n\n"
        res += lintres.text
        res += "\n"
        res += tree_context(rel_fname, code, lintres.lines)

        return res

    def py_lint(self, fname, rel_fname, code):
        basic_res = basic_lint(rel_fname, code)
        compile_res = lint_python_compile(fname, code)
        flake_res = self.flake8_lint(rel_fname)

        text = ""
        lines = set()
        for res in [basic_res, compile_res, flake_res]:
            if not res:
                continue
            if text:
                text += "\n"
            text += res.text
            lines.update(res.lines)

        if text or lines:
            return LintResult(text, lines)

    def flake8_lint(self, rel_fname):
        fatal = "E9,F821,F823,F831,F406,F407,F701,F702,F704,F706"
        flake8_cmd = [
            sys.executable,
            "-m",
            "flake8",
            f"--select={fatal}",
            "--show-source",
            "--isolated",
            rel_fname,
        ]

        text = f"## Executando: {' '.join(flake8_cmd)}\n\n"

        try:
            result = subprocess.run(
                flake8_cmd,
                capture_output=True,
                text=True,
                check=False,
                encoding=self.encoding,
                errors="replace",
                cwd=self.root,
            )
            errors = result.stdout + result.stderr
        except Exception as e:
            errors = f"Erro ao executar o flake8: {str(e)}"

        if not errors:
            return

        text += errors
        return self.errors_to_lint_result(rel_fname, text)


@dataclass
class LintResult:
    text: str
    lines: list


def lint_python_compile(fname, code):
    try:
        compile(code, fname, "exec")  # USE TRACEBACK BELOW HERE
        return
    except Exception as err:
        end_lineno = getattr(err, "end_lineno", err.lineno)
        line_numbers = list(range(err.lineno - 1, end_lineno))

        tb_lines = traceback.format_exception(type(err), err, err.__traceback__)
        last_file_i = 0

        target = "# USE TRACEBACK"
        target += " BELOW HERE"
        for i in range(len(tb_lines)):
            if target in tb_lines[i]:
                last_file_i = i
                break

        tb_lines = tb_lines[:1] + tb_lines[last_file_i + 1 :]

    res = "".join(tb_lines)
    return LintResult(text=res, lines=line_numbers)


def basic_lint(fname, code):
    """
    Usa o tree-sitter para procurar erros de sintaxe e exibi-los com o contexto da árvore.
    """

    lang = filename_to_lang(fname)
    if not lang:
        return

    # O linter do Tree-sitter não consegue trabalhar com TypeScript #1132
    if lang == "typescript":
        return

    try:
        parser = get_parser(lang)
    except Exception as err:
        print(f"Não foi possível carregar o parser: {err}")
        return

    tree = parser.parse(bytes(code, "utf-8"))

    try:
        errors = traverse_tree(tree.root_node)
    except RecursionError:
        print(f"Não foi possível executar o lint em {fname} devido a um RecursionError")
        return

    if not errors:
        return

    return LintResult(text="", lines=errors)


def tree_context(fname, code, line_nums):
    context = TreeContext(
        fname,
        code,
        color=False,
        line_number=True,
        child_context=False,
        last_line=False,
        margin=0,
        mark_lois=True,
        loi_pad=3,
        # header_max=30,
        show_top_of_file_parent_scope=False,
    )
    line_nums = set(line_nums)
    context.add_lines_of_interest(line_nums)
    context.add_context()
    plural = "s" if len(line_nums) > 1 else ""
    output = f"## Veja abaixo a{plural} linha{plural} relevante{plural} marcada{plural} com █.\n\n"
    output += fname + ":\n"
    output += context.format()

    return output


# Percorre a árvore para encontrar erros
def traverse_tree(node):
    errors = []
    if node.type == "ERROR" or node.is_missing:
        line_no = node.start_point[0]
        errors.append(line_no)

    for child in node.children:
        errors += traverse_tree(child)

    return errors


def find_filenames_and_linenums(text, fnames):
    """
    Procura no texto todas as ocorrências de <nome_do_arquivo>:\\d+ e cria uma lista delas,
    em que <nome_do_arquivo> é um dos nomes presentes na lista `fnames`.
    """
    pattern = re.compile(r"(\b(?:" + "|".join(re.escape(fname) for fname in fnames) + r"):\d+\b)")
    matches = pattern.findall(text)
    result = {}
    for match in matches:
        fname, linenum = match.rsplit(":", 1)
        if fname not in result:
            result[fname] = set()
        result[fname].add(int(linenum))
    return result


def main():
    """
    Função principal para processar arquivos fornecidos como argumentos da linha de comando.
    """
    if len(sys.argv) < 2:
        print("Uso: python linter.py <arquivo1> <arquivo2> ...")
        sys.exit(1)

    linter = Linter(root=os.getcwd())
    for file_path in sys.argv[1:]:
        errors = linter.lint(file_path)
        if errors:
            print(errors)


if __name__ == "__main__":
    main()
