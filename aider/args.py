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
    group = parser.add_argument_group("Git settings")
    group.add_argument(
        "--git",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable looking for a git repo (default: True)",
    )
    group.add_argument(
        "--gitignore",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable adding .aider* to .gitignore (default: True)",
    )
    group.add_argument(
        "--add-gitignore-files",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable the addition of files listed in .gitignore to Aider's editing scope.",
    )
    default_aiderignore_file = (
        os.path.join(git_root, ".aiderignore") if git_root else ".aiderignore"
    )

    group.add_argument(
        "--aiderignore",
        metavar="AIDERIGNORE",
        type=lambda path_str: resolve_aiderignore_path(path_str, git_root),
        default=default_aiderignore_file,
        help="Specify the aider ignore file (default: .aiderignore in git root)",
    ).complete = shtab.FILE
    group.add_argument(
        "--subtree-only",
        action="store_true",
        help="Only consider files in the current subtree of the git repository",
        default=False,
    )
    group.add_argument(
        "--auto-commits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable auto commit of LLM changes (default: True)",
    )
    group.add_argument(
        "--dirty-commits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable commits when repo is found dirty (default: True)",
    )
    group.add_argument(
        "--attribute-author",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Attribute aider code changes in the git author name (default: True). If explicitly set"
            " to True, overrides --attribute-co-authored-by precedence."
        ),
    )
    group.add_argument(
        "--attribute-committer",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Attribute aider commits in the git committer name (default: True). If explicitly set"
            " to True, overrides --attribute-co-authored-by precedence for aider edits."
        ),
    )
    group.add_argument(
        "--attribute-commit-message-author",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Prefix commit messages with 'aider: ' if aider authored the changes (default: False)",
    )
    group.add_argument(
        "--attribute-commit-message-committer",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Prefix all commit messages with 'aider: ' (default: False)",
    )
    group.add_argument(
        "--attribute-co-authored-by",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Attribute aider edits using the Co-authored-by trailer in the commit message"
            " (default: True). If True, this takes precedence over default --attribute-author and"
            " --attribute-committer behavior unless they are explicitly set to True."
        ),
    )
    group.add_argument(
        "--git-commit-verify",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable git pre-commit hooks with --no-verify (default: False)",
    )
    group.add_argument(
        "--commit",
        action="store_true",
        help="Commit all pending changes with a suitable commit message, then exit",
        default=False,
    )
    group.add_argument(
        "--commit-prompt",
        metavar="PROMPT",
        help="Specify a custom prompt for generating commit messages",
    )
    group.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Perform a dry run without modifying files (default: False)",
    )
    group.add_argument(
        "--skip-sanity-check-repo",
        action="store_true",
        help="Skip the sanity check for the git repository (default: False)",
        default=False,
    )
    group.add_argument(
        "--watch-files",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable watching files for ai coding comments (default: False)",
    )
    group = parser.add_argument_group("Fixing and committing")
    group.add_argument(
        "--lint",
        action="store_true",
        help="Lint and fix provided files, or dirty files if none provided",
        default=False,
    )
    group.add_argument(
        "--lint-cmd",
        action="append",
        help=(
            'Specify lint commands to run for different languages, eg: "python: flake8'
            ' --select=..." (can be used multiple times)'
        ),
        default=[],
    )
    group.add_argument(
        "--auto-lint",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable automatic linting after changes (default: True)",
    )
    group.add_argument(
        "--test-cmd",
        help="Specify command to run tests",
        default=[],
    )
    group.add_argument(
        "--auto-test",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable automatic testing after changes (default: False)",
    )
    group.add_argument(
        "--test",
        action="store_true",
        help="Run tests, fix problems found and then exit",
        default=False,
    )

    ##########
    group = parser.add_argument_group("Analytics")
    group.add_argument(
        "--analytics",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable analytics for current session (default: random)",
    )
    group.add_argument(
        "--analytics-log",
        metavar="ANALYTICS_LOG_FILE",
        help="Specify a file to log analytics events",
    ).complete = shtab.FILE
    group.add_argument(
        "--analytics-disable",
        action="store_true",
        help="Permanently disable analytics",
        default=False,
    )
    group.add_argument(
        "--analytics-posthog-host",
        metavar="ANALYTICS_POSTHOG_HOST",
        help="Send analytics to custom PostHog instance",
    )
    group.add_argument(
        "--analytics-posthog-project-api-key",
        metavar="ANALYTICS_POSTHOG_PROJECT_API_KEY",
        help="Send analytics to custom PostHog project",
    )

    #########
    group = parser.add_argument_group("Upgrading")
    group.add_argument(
        "--just-check-update",
        action="store_true",
        help="Check for updates and return status in the exit code",
        default=False,
    )
    group.add_argument(
        "--check-update",
        action=argparse.BooleanOptionalAction,
        help="Check for new aider versions on launch",
        default=True,
    )
    group.add_argument(
        "--show-release-notes",
        action=argparse.BooleanOptionalAction,
        help="Show release notes on first run of new version (default: None, ask user)",
        default=None,
    )
    group.add_argument(
        "--install-main-branch",
        action="store_true",
        help="Install the latest version from the main branch",
        default=False,
    )
    group.add_argument(
        "--upgrade",
        "--update",
        action="store_true",
        help="Upgrade aider to the latest version from PyPI",
        default=False,
    )
    group.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version number and exit",
    )

    ##########
    group = parser.add_argument_group("Modes")
    group.add_argument(
        "--message",
        "--msg",
        "-m",
        metavar="COMMAND",
        help=(
            "Specify a single message to send the LLM, process reply then exit (disables chat mode)"
        ),
    )
    group.add_argument(
        "--message-file",
        "-f",
        metavar="MESSAGE_FILE",
        help=(
            "Specify a file containing the message to send the LLM, process reply, then exit"
            " (disables chat mode)"
        ),
    ).complete = shtab.FILE
    group.add_argument(
        "--gui",
        "--browser",
        action=argparse.BooleanOptionalAction,
        help="Run aider in your browser (default: False)",
        default=False,
    )
    group.add_argument(
        "--copy-paste",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable automatic copy/paste of chat between aider and web UI (default: False)",
    )
    group.add_argument(
        "--apply",
        metavar="FILE",
        help="Apply the changes from the given file instead of running the chat (debug)",
    ).complete = shtab.FILE
    group.add_argument(
        "--apply-clipboard-edits",
        action="store_true",
        help="Apply clipboard contents as edits using the main model's editor format",
        default=False,
    )
    group.add_argument(
        "--exit",
        action="store_true",
        help="Do all startup activities then exit before accepting user input (debug)",
        default=False,
    )
    group.add_argument(
        "--show-repo-map",
        action="store_true",
        help="Print the repo map and exit (debug)",
        default=False,
    )
    group.add_argument(
        "--show-prompts",
        action="store_true",
        help="Print the system prompts and exit (debug)",
        default=False,
    )

    ##########
    group = parser.add_argument_group("Voice settings")
    group.add_argument(
        "--voice-format",
        metavar="VOICE_FORMAT",
        default="wav",
        choices=["wav", "mp3", "webm"],
        help="Audio format for voice recording (default: wav). webm and mp3 require ffmpeg",
    )
    group.add_argument(
        "--voice-language",
        metavar="VOICE_LANGUAGE",
        default="en",
        help="Specify the language for voice using ISO 639-1 code (default: auto)",
    )
    group.add_argument(
        "--voice-input-device",
        metavar="VOICE_INPUT_DEVICE",
        default=None,
        help="Specify the input device name for voice recording",
    )

    ######
    group = parser.add_argument_group("Other settings")
    group.add_argument(
        "--disable-playwright",
        action="store_true",
        help="Never prompt for or attempt to install Playwright for web scraping (default: False).",
        default=False,
    )
    group.add_argument(
        "--file",
        action="append",
        metavar="FILE",
        help="specify a file to edit (can be used multiple times)",
    ).complete = shtab.FILE
    group.add_argument(
        "--read",
        action="append",
        metavar="FILE",
        help="specify a read-only file (can be used multiple times)",
    ).complete = shtab.FILE
    group.add_argument(
        "--vim",
        action="store_true",
        help="Use VI editing mode in the terminal (default: False)",
        default=False,
    )
    group.add_argument(
        "--chat-language",
        metavar="CHAT_LANGUAGE",
        default=None,
        help="Specify the language to use in the chat (default: None, uses system settings)",
    )
    group.add_argument(
        "--commit-language",
        metavar="COMMIT_LANGUAGE",
        default=None,
        help="Specify the language to use in the commit message (default: None, user language)",
    )
    group.add_argument(
        "--yes-always",
        action="store_true",
        help="Always say yes to every confirmation",
        default=None,
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
        default=False,
    )
    group.add_argument(
        "--load",
        metavar="LOAD_FILE",
        help="Load and execute /commands from a file on launch",
    ).complete = shtab.FILE
    group.add_argument(
        "--encoding",
        default="utf-8",
        help="Specify the encoding for input and output (default: utf-8)",
    )
    group.add_argument(
        "--line-endings",
        choices=["platform", "lf", "crlf"],
        default="platform",
        help="Line endings to use when writing files (default: platform)",
    )
    group.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        metavar="CONFIG_FILE",
        help=(
            "Specify the config file (default: search for .aider.conf.yml in git root, cwd"
            " or home directory)"
        ),
    ).complete = shtab.FILE
    # This is a duplicate of the argument in the preparser and is a no-op by this time of
    # argument parsing, but it's here so that the help is displayed as expected.
    group.add_argument(
        "--env-file",
        metavar="ENV_FILE",
        default=default_env_file(git_root),
        help="Specify the .env file to load (default: .env in git root)",
    ).complete = shtab.FILE
    group.add_argument(
        "--suggest-shell-commands",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable suggesting shell commands (default: True)",
    )
    group.add_argument(
        "--fancy-input",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable fancy input with history and completion (default: True)",
    )
    group.add_argument(
        "--multiline",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable multi-line input mode with Meta-Enter to submit (default: False)",
    )
    group.add_argument(
        "--notifications",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Enable/disable terminal bell notifications when LLM responses are ready (default:"
            " False)"
        ),
    )
    group.add_argument(
        "--notifications-command",
        metavar="COMMAND",
        default=None,
        help=(
            "Specify a command to run for notifications instead of the terminal bell. If not"
            " specified, a default command for your OS may be used."
        ),
    )
    group.add_argument(
        "--detect-urls",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable detection and offering to add URLs to chat (default: True)",
    )
    group.add_argument(
        "--editor",
        help="Specify which editor to use for the /editor command",
    )

    supported_shells_list = sorted(list(shtab.SUPPORTED_SHELLS))
    group.add_argument(
        "--shell-completions",
        metavar="SHELL",
        choices=supported_shells_list,
        help=(
            "Print shell completion script for the specified SHELL and exit. Supported shells:"
            f" {', '.join(supported_shells_list)}. Example: aider --shell-completions bash"
        ),
    )

    ##########
    group = parser.add_argument_group("Deprecated model settings")
    # Add deprecated model shortcut arguments
    add_deprecated_model_args(parser, group)

    return parser


def get_md_help():
    os.environ["COLUMNS"] = "70"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # This instantiates all the action.env_var values
    parser.parse_known_args()

    parser.formatter_class = MarkdownHelpFormatter

    return argparse.ArgumentParser.format_help(parser)


def get_sample_yaml():
    os.environ["COLUMNS"] = "100"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # This instantiates all the action.env_var values
    parser.parse_known_args()

    parser.formatter_class = YamlHelpFormatter

    return argparse.ArgumentParser.format_help(parser)


def get_sample_dotenv():
    os.environ["COLUMNS"] = "120"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # This instantiates all the action.env_var values
    parser.parse_known_args()

    parser.formatter_class = DotEnvFormatter

    return argparse.ArgumentParser.format_help(parser)


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "yaml"  # Default to yaml if no command is given

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
                print(f"Error: Unsupported shell '{shell}'.", file=sys.stderr)
                print(f"Supported shells are: {', '.join(shtab.SUPPORTED_SHELLS)}", file=sys.stderr)
                sys.exit(1)
            parser = get_parser([], None)
            parser.prog = "aider"  # Set the program name on the parser
            print(shtab.complete(parser, shell=shell))
        else:
            print("Error: Please specify a shell for completion.", file=sys.stderr)
            print(f"Usage: python {sys.argv[0]} completion <shell_name>", file=sys.stderr)
            print(f"Supported shells are: {', '.join(shtab.SUPPORTED_SHELLS)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default to YAML for any other unrecognized argument, or if 'yaml' was explicitly passed
        print(get_sample_yaml())


if __name__ == "__main__":
    status = main()
    sys.exit(status)
