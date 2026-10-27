#!/usr/bin/env python

import argparse
import os
import sys
from pathlib import Path

import configargparse
import shtab

from aider import __version__
from aider.args_formatter import (
    DotEnvFormatter,
    MarkdownHelpFormatter,
    YamlHelpFormatter,
)
from aider.deprecated import add_deprecated_model_args

from .dump import dump  # noqa: F401


def resolve_aiderignore_path(path_str, git_root=None):
    path = Path(path_str)
    if path.is_absolute():
        return str(path)
    elif git_root:
        return str(Path(git_root) / path)
    return str(path)


def default_env_file(git_root):
    return os.path.join(git_root, ".env") if git_root else ".env"


def get_parser(default_config_files, git_root):
    parser = configargparse.ArgumentParser(
        description="aider é seu assistente de programação com IA no terminal",
        add_config_file_help=True,
        default_config_files=default_config_files,
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        auto_env_var_prefix="AIDER_",
    )
    # Formatos de edição válidos para validação do argparse e autocompletar do shtab.
    # Obtém os formatos dinamicamente das classes de codificação registradas, para que
    # a lista continue atualizada quando novos formatos forem adicionados.
    from aider import coders as _aider_coders

    edit_format_choices = sorted(
        {
            c.edit_format
            for c in _aider_coders.__all__
            if hasattr(c, "edit_format") and c.edit_format is not None
        }
    )
    group = parser.add_argument_group("Modelo principal")
    group.add_argument(
        "files", metavar="FILE", nargs="*", help="Arquivos para editar com um modelo de linguagem (opcional)"
    ).complete = shtab.FILE
    group.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        help="Especifica o modelo usado na conversa principal",
    )

    ##########
    group = parser.add_argument_group("Chaves de API e configurações")
    group.add_argument(
        "--openai-api-key",
        help="Especifica a chave de API da OpenAI",
    )
    group.add_argument(
        "--anthropic-api-key",
        help="Especifica a chave de API da Anthropic",
    )
    group.add_argument(
        "--openai-api-base",
        help="Especifica a URL base da API",
    )
    group.add_argument(
        "--openai-api-type",
        help="(obsoleto, use --set-env OPENAI_API_TYPE=<value>)",
    )
    group.add_argument(
        "--openai-api-version",
        help="(obsoleto, use --set-env OPENAI_API_VERSION=<value>)",
    )
    group.add_argument(
        "--openai-api-deployment-id",
        help="(obsoleto, use --set-env OPENAI_API_DEPLOYMENT_ID=<value>)",
    )
    group.add_argument(
        "--openai-organization-id",
        help="(obsoleto, use --set-env OPENAI_ORGANIZATION=<value>)",
    )
    group.add_argument(
        "--set-env",
        action="append",
        metavar="ENV_VAR_NAME=value",
        help="Define uma variável de ambiente (para configurar APIs; pode ser usado várias vezes)",
        default=[],
    )
    group.add_argument(
        "--api-key",
        action="append",
        metavar="PROVIDER=KEY",
        help=(
            "Define uma chave de API para um provedor (ex.: --api-key provider=<key> define"
            " PROVIDER_API_KEY=<key>)"
        ),
        default=[],
    )
    group = parser.add_argument_group("Configurações de modelos")
    group.add_argument(
        "--list-models",
        "--models",
        metavar="MODEL",
        help="Lista modelos conhecidos cujo nome corresponde a MODEL (mesmo parcialmente)",
    )
    group.add_argument(
        "--model-settings-file",
        metavar="MODEL_SETTINGS_FILE",
        default=".aider.model.settings.yml",
        help="Especifica um arquivo de configurações do aider para modelos desconhecidos",
    ).complete = shtab.FILE
    group.add_argument(
        "--model-metadata-file",
        metavar="MODEL_METADATA_FILE",
        default=".aider.model.metadata.json",
        help="Especifica um arquivo com janela de contexto e custos de modelos desconhecidos",
    ).complete = shtab.FILE
    group.add_argument(
        "--alias",
        action="append",
        metavar="ALIAS:MODEL",
        help="Adiciona um apelido de modelo (pode ser usado várias vezes)",
    )
    group.add_argument(
        "--reasoning-effort",
        type=str,
        help="Define o parâmetro de API reasoning_effort (padrão: não definido)",
    )
    group.add_argument(
        "--thinking-tokens",
        type=str,
        help=(
            "Define o limite de tokens de raciocínio para modelos compatíveis. Use 0 para desativar. (padrão:"
            " não definido)"
        ),
    )
    group.add_argument(
        "--verify-ssl",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verifica o certificado SSL ao conectar aos modelos (padrão: True)",
    )
    group.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Tempo limite em segundos para chamadas de API (padrão: None)",
    )
    group.add_argument(
        "--edit-format",
        "--chat-mode",
        metavar="EDIT_FORMAT",
        choices=edit_format_choices,
        default=None,
        help="Especifica o formato de edição usado pelo modelo (padrão: depende do modelo)",
    )
    group.add_argument(
        "--architect",
        action="store_const",
        dest="edit_format",
        const="architect",
        help="Usa o formato de edição arquiteto na conversa principal",
    )
    group.add_argument(
        "--auto-accept-architect",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a aceitação automática de alterações do arquiteto (padrão: True)",
    )
    group.add_argument(
        "--weak-model",
        metavar="WEAK_MODEL",
        default=None,
        help=(
            "Especifica o modelo para mensagens de commit e resumos do histórico da conversa (padrão"
            " depende de --model)"
        ),
    )
    group.add_argument(
        "--editor-model",
        metavar="EDITOR_MODEL",
        default=None,
        help="Especifica o modelo para tarefas de edição (padrão: depende de --model)",
    )
    group.add_argument(
        "--editor-edit-format",
        metavar="EDITOR_EDIT_FORMAT",
        choices=edit_format_choices,
        default=None,
        help="Especifica o formato de edição do modelo editor (padrão: depende do modelo editor)",
    )
    group.add_argument(
        "--show-model-warnings",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Trabalha apenas com modelos que possuem metadados disponíveis (padrão: True)",
    )
    group.add_argument(
        "--check-model-accepts-settings",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Verifica se o modelo aceita configurações como reasoning_effort/thinking_tokens (padrão: True)"
        ),
    )
    group.add_argument(
        "--max-chat-history-tokens",
        type=int,
        default=None,
        help=(
            "Limite flexível de tokens do histórico da conversa, após o qual começa o resumo."
            " Se não informado, usa max_chat_history_tokens do modelo como padrão."
        ),
    )

    ##########
    group = parser.add_argument_group("Configurações de cache")
    group.add_argument(
        "--cache-prompts",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa o cache de prompts (padrão: False)",
    )
    group.add_argument(
        "--cache-keepalive-pings",
        type=int,
        default=0,
        help="Número de pings em intervalos de 5 minutos para manter o cache de prompts ativo (padrão: 0)",
    )

    ##########
    group = parser.add_argument_group("Configurações do mapa do repositório")
    group.add_argument(
        "--map-tokens",
        type=int,
        default=None,
        help="Quantidade sugerida de tokens para o mapa do repositório; use 0 para desativar",
    )
    group.add_argument(
        "--map-refresh",
        choices=["auto", "always", "files", "manual"],
        default="auto",
        help=(
            "Controla a frequência de atualização do mapa do repositório. Opções: auto, always, files, manual"
            " (padrão: auto)"
        ),
    )
    group.add_argument(
        "--map-multiplier-no-files",
        type=float,
        default=2,
        help="Multiplicador de tokens do mapa quando nenhum arquivo é informado (padrão: 2)",
    )

    ##########
    group = parser.add_argument_group("Arquivos de histórico")
    default_input_history_file = (
        os.path.join(git_root, ".aider.input.history") if git_root else ".aider.input.history"
    )
    default_chat_history_file = (
        os.path.join(git_root, ".aider.chat.history.md") if git_root else ".aider.chat.history.md"
    )
    group.add_argument(
        "--input-history-file",
        metavar="INPUT_HISTORY_FILE",
        default=default_input_history_file,
        help=f"Especifica o arquivo do histórico de entradas da conversa (padrão: {default_input_history_file})",
    ).complete = shtab.FILE
    group.add_argument(
        "--chat-history-file",
        metavar="CHAT_HISTORY_FILE",
        default=default_chat_history_file,
        help=f"Especifica o arquivo do histórico da conversa (padrão: {default_chat_history_file})",
    ).complete = shtab.FILE
    group.add_argument(
        "--restore-chat-history",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Restaura as mensagens anteriores do histórico da conversa (padrão: False)",
    )
    group.add_argument(
        "--llm-history-file",
        metavar="LLM_HISTORY_FILE",
        default=None,
        help="Registra a conversa com o modelo neste arquivo (por exemplo, .aider.llm.history)",
    ).complete = shtab.FILE

    ##########
    group = parser.add_argument_group("Configurações de saída")
    group.add_argument(
        "--dark-mode",
        action="store_true",
        help="Usa cores adequadas a terminais com fundo escuro (padrão: False)",
        default=False,
    )
    group.add_argument(
        "--light-mode",
        action="store_true",
        help="Usa cores adequadas a terminais com fundo claro (padrão: False)",
        default=False,
    )
    group.add_argument(
        "--pretty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a saída formatada e colorida (padrão: True)",
    )
    group.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa respostas transmitidas em tempo real (padrão: True)",
    )
    group.add_argument(
        "--user-input-color",
        default="#00cc00",
        help="Define a cor da entrada do usuário (padrão: #00cc00)",
    )
    group.add_argument(
        "--tool-output-color",
        default=None,
        help="Define a cor da saída das ferramentas (padrão: None)",
    )
    group.add_argument(
        "--tool-error-color",
        default="#FF2222",
        help="Define a cor das mensagens de erro das ferramentas (padrão: #FF2222)",
    )
    group.add_argument(
        "--tool-warning-color",
        default="#FFA500",
        help="Define a cor dos avisos das ferramentas (padrão: #FFA500)",
    )
    group.add_argument(
        "--assistant-output-color",
        default="#0088ff",
        help="Define a cor das respostas do assistente (padrão: #0088ff)",
    )
    group.add_argument(
        "--completion-menu-color",
        metavar="COLOR",
        default=None,
        help="Define a cor do menu de autocompletar (padrão: cor do texto do terminal)",
    )
    group.add_argument(
        "--completion-menu-bg-color",
        metavar="COLOR",
        default=None,
        help="Define a cor de fundo do menu de autocompletar (padrão: cor de fundo do terminal)",
    )
    group.add_argument(
        "--completion-menu-current-color",
        metavar="COLOR",
        default=None,
        help="Define a cor do item selecionado no menu de autocompletar (padrão: cor de fundo do terminal)",
    )
    group.add_argument(
        "--completion-menu-current-bg-color",
        metavar="COLOR",
        default=None,
        help="Define a cor de fundo do item selecionado no menu de autocompletar (padrão: cor do texto do terminal)",
    )
    group.add_argument(
        "--code-theme",
        default="default",
        help=(
            "Define o tema do código Markdown (padrão: default; outras opções incluem monokai,"
            " solarized-dark, solarized-light ou um estilo integrado do Pygments;"
            " consulte https://pygments.org/styles para ver os temas disponíveis)"
        ),
    )
    group.add_argument(
        "--show-diffs",
        action="store_true",
        help="Exibe as diferenças ao criar commits (padrão: False)",
        default=False,
    )

    ##########
    group = parser.add_argument_group("Configurações do Git")
    group.add_argument(
        "--git",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a busca por um repositório Git (padrão: True)",
    )
    group.add_argument(
        "--gitignore",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a inclusão de .aider* no .gitignore (padrão: True)",
    )
    group.add_argument(
        "--add-gitignore-files",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa/desativa a inclusão de arquivos listados no .gitignore no escopo de edição do aider.",
    )
    default_aiderignore_file = (
        os.path.join(git_root, ".aiderignore") if git_root else ".aiderignore"
    )

    group.add_argument(
        "--aiderignore",
        metavar="AIDERIGNORE",
        type=lambda path_str: resolve_aiderignore_path(path_str, git_root),
        default=default_aiderignore_file,
        help="Especifica o arquivo de exclusões do aider (padrão: .aiderignore na raiz do Git)",
    ).complete = shtab.FILE
    group.add_argument(
        "--subtree-only",
        action="store_true",
        help="Considera apenas arquivos da subárvore atual do repositório Git",
        default=False,
    )
    group.add_argument(
        "--auto-commits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa commits automáticos das alterações do modelo (padrão: True)",
    )
    group.add_argument(
        "--dirty-commits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa commits quando o repositório possui alterações pendentes (padrão: True)",
    )
    group.add_argument(
        "--attribute-author",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Atribui alterações do aider ao nome do autor no Git (padrão: True). Se definido explicitamente"
            " como True, tem prioridade sobre --attribute-co-authored-by."
        ),
    )
    group.add_argument(
        "--attribute-committer",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Atribui commits do aider ao nome de quem realizou o commit no Git (padrão: True). Se definido explicitamente"
            " como True, tem prioridade sobre --attribute-co-authored-by para alterações do aider."
        ),
    )
    group.add_argument(
        "--attribute-commit-message-author",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Adiciona 'aider: ' ao início da mensagem de commit se o aider fez as alterações (padrão: False)",
    )
    group.add_argument(
        "--attribute-commit-message-committer",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Adiciona 'aider: ' ao início de todas as mensagens de commit (padrão: False)",
    )
    group.add_argument(
        "--attribute-co-authored-by",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Atribui alterações do aider usando o rodapé Co-authored-by na mensagem de commit"
            " (padrão: True). Quando True, tem prioridade sobre os padrões de --attribute-author e"
            " --attribute-committer, a menos que sejam definidos explicitamente como True."
        ),
    )
    group.add_argument(
        "--git-commit-verify",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa/desativa hooks de pré-commit do Git com --no-verify (padrão: False)",
    )
    group.add_argument(
        "--commit",
        action="store_true",
        help="Cria um commit com todas as alterações pendentes e uma mensagem adequada, depois encerra",
        default=False,
    )
    group.add_argument(
        "--commit-prompt",
        metavar="PROMPT",
        help="Especifica um prompt personalizado para gerar mensagens de commit",
    )
    group.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Executa uma simulação sem modificar arquivos (padrão: False)",
    )
    group.add_argument(
        "--skip-sanity-check-repo",
        action="store_true",
        help="Ignora a verificação de integridade do repositório Git (padrão: False)",
        default=False,
    )
    group.add_argument(
        "--watch-files",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa/desativa o monitoramento de arquivos para comentários de programação com IA (padrão: False)",
    )
    group = parser.add_argument_group("Correções e commits")
    group.add_argument(
        "--lint",
        action="store_true",
        help="Verifica e corrige os arquivos informados ou, na ausência deles, os arquivos modificados",
        default=False,
    )
    group.add_argument(
        "--lint-cmd",
        action="append",
        help=(
            'Especifica comandos de lint para diferentes linguagens, ex.: "python: flake8'
            ' --select=..." (pode ser usado várias vezes)'
        ),
        default=[],
    )
    group.add_argument(
        "--auto-lint",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a verificação automática de lint após alterações (padrão: True)",
    )
    group.add_argument(
        "--test-cmd",
        help="Especifica o comando para executar os testes",
        default=[],
    )
    group.add_argument(
        "--auto-test",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa/desativa a execução automática de testes após alterações (padrão: False)",
    )
    group.add_argument(
        "--test",
        action="store_true",
        help="Executa os testes, corrige os problemas encontrados e depois encerra",
        default=False,
    )

    ##########
    group = parser.add_argument_group("Análise de uso")
    group.add_argument(
        "--analytics",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ativa/desativa a análise de uso nesta sessão (padrão: aleatório)",
    )
    group.add_argument(
        "--analytics-log",
        metavar="ANALYTICS_LOG_FILE",
        help="Especifica um arquivo para registrar eventos de análise de uso",
    ).complete = shtab.FILE
    group.add_argument(
        "--analytics-disable",
        action="store_true",
        help="Desativa permanentemente a análise de uso",
        default=False,
    )
    group.add_argument(
        "--analytics-posthog-host",
        metavar="ANALYTICS_POSTHOG_HOST",
        help="Envia dados de análise de uso para uma instância personalizada do PostHog",
    )
    group.add_argument(
        "--analytics-posthog-project-api-key",
        metavar="ANALYTICS_POSTHOG_PROJECT_API_KEY",
        help="Envia dados de análise de uso para um projeto personalizado do PostHog",
    )

    #########
    group = parser.add_argument_group("Atualizações")
    group.add_argument(
        "--just-check-update",
        action="store_true",
        help="Verifica se há atualizações e informa o resultado no código de saída",
        default=False,
    )
    group.add_argument(
        "--check-update",
        action=argparse.BooleanOptionalAction,
        help="Verifica se há novas versões do aider ao iniciar",
        default=True,
    )
    group.add_argument(
        "--show-release-notes",
        action=argparse.BooleanOptionalAction,
        help="Exibe as notas de versão na primeira execução da nova versão (padrão: None, perguntar ao usuário)",
        default=None,
    )
    group.add_argument(
        "--install-main-branch",
        action="store_true",
        help="Instala a versão mais recente da branch principal",
        default=False,
    )
    group.add_argument(
        "--upgrade",
        "--update",
        action="store_true",
        help="Atualiza o aider para a versão mais recente disponível no PyPI",
        default=False,
    )
    group.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Exibe o número da versão e encerra",
    )

    ##########
    group = parser.add_argument_group("Modos de execução")
    group.add_argument(
        "--message",
        "--msg",
        "-m",
        metavar="COMMAND",
        help=(
            "Envia uma única mensagem ao modelo, processa a resposta e encerra (desativa o modo de chat)"
        ),
    )
    group.add_argument(
        "--message-file",
        "-f",
        metavar="MESSAGE_FILE",
        help=(
            "Especifica um arquivo com a mensagem para o modelo, processa a resposta e encerra"
            " (desativa o modo de chat)"
        ),
    ).complete = shtab.FILE
    group.add_argument(
        "--gui",
        "--browser",
        action=argparse.BooleanOptionalAction,
        help="Executa o aider no navegador (padrão: False)",
        default=False,
    )
    group.add_argument(
        "--copy-paste",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa a cópia e colagem automáticas do chat entre o aider e a interface web (padrão: False)",
    )
    group.add_argument(
        "--apply",
        metavar="FILE",
        help="Aplica as alterações do arquivo informado em vez de iniciar o chat (depuração)",
    ).complete = shtab.FILE
    group.add_argument(
        "--apply-clipboard-edits",
        action="store_true",
        help="Aplica o conteúdo da área de transferência como edições no formato do modelo principal",
        default=False,
    )
    group.add_argument(
        "--exit",
        action="store_true",
        help="Executa as tarefas de inicialização e encerra antes de receber entradas do usuário (depuração)",
        default=False,
    )
    group.add_argument(
        "--show-repo-map",
        action="store_true",
        help="Exibe o mapa do repositório e encerra (depuração)",
        default=False,
    )
    group.add_argument(
        "--show-prompts",
        action="store_true",
        help="Exibe os prompts de sistema e encerra (depuração)",
        default=False,
    )

    ##########
    group = parser.add_argument_group("Configurações de voz")
    group.add_argument(
        "--voice-format",
        metavar="VOICE_FORMAT",
        default="wav",
        choices=["wav", "mp3", "webm"],
        help="Formato de áudio para gravação de voz (padrão: wav). webm e mp3 exigem ffmpeg",
    )
    group.add_argument(
        "--voice-language",
        metavar="VOICE_LANGUAGE",
        default="en",
        help="Especifica o idioma da voz pelo código ISO 639-1 (padrão: auto)",
    )
    group.add_argument(
        "--voice-input-device",
        metavar="VOICE_INPUT_DEVICE",
        default=None,
        help="Especifica o nome do dispositivo de entrada para gravação de voz",
    )

    ######
    group = parser.add_argument_group("Outras configurações")
    group.add_argument(
        "--disable-playwright",
        action="store_true",
        help="Nunca solicita nem tenta instalar o Playwright para extração de dados da web (padrão: False).",
        default=False,
    )
    group.add_argument(
        "--file",
        action="append",
        metavar="FILE",
        help="Especifica um arquivo para editar (pode ser usado várias vezes)",
    ).complete = shtab.FILE
    group.add_argument(
        "--read",
        action="append",
        metavar="FILE",
        help="Especifica um arquivo somente leitura (pode ser usado várias vezes)",
    ).complete = shtab.FILE
    group.add_argument(
        "--vim",
        action="store_true",
        help="Usa o modo de edição VI no terminal (padrão: False)",
        default=False,
    )
    group.add_argument(
        "--chat-language",
        metavar="CHAT_LANGUAGE",
        default=None,
        help="Especifica o idioma usado no chat (padrão: None, usa as configurações do sistema)",
    )
    group.add_argument(
        "--commit-language",
        metavar="COMMIT_LANGUAGE",
        default=None,
        help="Especifica o idioma das mensagens de commit (padrão: None, idioma do usuário)",
    )
    group.add_argument(
        "--yes-always",
        action="store_true",
        help="Responde sim automaticamente a todas as confirmações",
        default=None,
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Ativa a saída detalhada",
        default=False,
    )
    group.add_argument(
        "--load",
        metavar="LOAD_FILE",
        help="Carrega e executa /commands de um arquivo ao iniciar",
    ).complete = shtab.FILE
    group.add_argument(
        "--encoding",
        default="utf-8",
        help="Especifica a codificação de entrada e saída (padrão: utf-8)",
    )
    group.add_argument(
        "--line-endings",
        choices=["platform", "lf", "crlf"],
        default="platform",
        help="Define as terminações de linha ao gravar arquivos (padrão: platform)",
    )
    group.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        metavar="CONFIG_FILE",
        help=(
            "Especifica o arquivo de configuração (padrão: procura .aider.conf.yml na raiz do Git, no diretório atual"
            " ou na pasta pessoal)"
        ),
    ).complete = shtab.FILE
    # Este argumento duplica o do pré-analisador e já não produz efeito nesta etapa
    # da análise de argumentos; ele permanece para exibir a ajuda corretamente.
    group.add_argument(
        "--env-file",
        metavar="ENV_FILE",
        default=default_env_file(git_root),
        help="Especifica o arquivo .env a carregar (padrão: .env na raiz do Git)",
    ).complete = shtab.FILE
    group.add_argument(
        "--suggest-shell-commands",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa sugestões de comandos do shell (padrão: True)",
    )
    group.add_argument(
        "--fancy-input",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a entrada avançada com histórico e autocompletar (padrão: True)",
    )
    group.add_argument(
        "--multiline",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ativa/desativa a entrada em várias linhas com Meta-Enter para enviar (padrão: False)",
    )
    group.add_argument(
        "--notifications",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Ativa/desativa avisos sonoros no terminal quando as respostas do modelo estiverem prontas (padrão:"
            " False)"
        ),
    )
    group.add_argument(
        "--notifications-command",
        metavar="COMMAND",
        default=None,
        help=(
            "Especifica um comando para notificações em vez do aviso sonoro do terminal. Se não for"
            " informado, poderá ser usado um comando padrão do sistema operacional."
        ),
    )
    group.add_argument(
        "--detect-urls",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ativa/desativa a detecção e a sugestão de adicionar URLs ao chat (padrão: True)",
    )
    group.add_argument(
        "--editor",
        help="Especifica o editor usado pelo comando /editor",
    )

    supported_shells_list = sorted(list(shtab.SUPPORTED_SHELLS))
    group.add_argument(
        "--shell-completions",
        metavar="SHELL",
        choices=supported_shells_list,
        help=(
            "Exibe o script de autocompletar para o SHELL informado e encerra. Shells compatíveis:"
            f" {', '.join(supported_shells_list)}. Exemplo: aider --shell-completions bash"
        ),
    )

    ##########
    group = parser.add_argument_group("Configurações obsoletas de modelos")
    # Adiciona os atalhos obsoletos de modelos
    add_deprecated_model_args(parser, group)

    return parser


def get_md_help():
    os.environ["COLUMNS"] = "70"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # Inicializa todos os valores de action.env_var
    parser.parse_known_args()

    parser.formatter_class = MarkdownHelpFormatter

    return argparse.ArgumentParser.format_help(parser)


def get_sample_yaml():
    os.environ["COLUMNS"] = "100"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # Inicializa todos os valores de action.env_var
    parser.parse_known_args()

    parser.formatter_class = YamlHelpFormatter

    return argparse.ArgumentParser.format_help(parser)


def get_sample_dotenv():
    os.environ["COLUMNS"] = "120"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # Inicializa todos os valores de action.env_var
    parser.parse_known_args()

    parser.formatter_class = DotEnvFormatter

    return argparse.ArgumentParser.format_help(parser)


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "yaml"  # Usa yaml por padrão quando nenhum comando é informado

    if command == "md":
        print(get_md_help())
    elif command == "dotenv":
        print(get_sample_dotenv())
    elif command == "yaml":
        print(get_sample_yaml())
    elif command == "completion":
        if len(sys.argv) > 2:
            shell = sys.argv[2]
            if shell not in shtab.SUPPORTED_SHELLS:
                print(f"Erro: shell não compatível '{shell}'.", file=sys.stderr)
                print(f"Shells compatíveis: {', '.join(shtab.SUPPORTED_SHELLS)}", file=sys.stderr)
                sys.exit(1)
            parser = get_parser([], None)
            parser.prog = "aider"  # Define o nome do programa no analisador
            print(shtab.complete(parser, shell=shell))
        else:
            print("Erro: informe um shell para o autocompletar.", file=sys.stderr)
            print(f"Uso: python {sys.argv[0]} completion <shell_name>", file=sys.stderr)
            print(f"Shells compatíveis: {', '.join(shtab.SUPPORTED_SHELLS)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Usa YAML para argumentos não reconhecidos ou quando 'yaml' é informado explicitamente
        print(get_sample_yaml())


if __name__ == "__main__":
    status = main()
    sys.exit(status)
