"""
Módulo de editor para lidar com interações com o editor de texto do sistema.

Este módulo fornece funcionalidades para:
- Descobrir e iniciar o editor de texto configurado no sistema
- Criar e gerenciar arquivos temporários para edição
- Lidar com preferências de editor definidas por variáveis de ambiente
- Oferecer suporte a operações de editor entre diferentes plataformas
"""

import os
import platform
import subprocess
import tempfile

from rich.console import Console

from aider.dump import dump  # noqa

DEFAULT_EDITOR_NIX = "vi"
DEFAULT_EDITOR_OS_X = "vim"
DEFAULT_EDITOR_WINDOWS = "notepad"

console = Console()


def print_status_message(success, message, style=None):
    """
    Exibe uma mensagem de status com a formatação apropriada.

    :param success: Indica se a operação foi bem-sucedida
    :param message: A mensagem a ser exibida
    :param style: Substituição opcional de estilo. Se for None, usa verde em caso de sucesso e vermelho em caso de falha
    """
    if style is None:
        style = "bold green" if success else "bold red"
    console.print(message, style=style)
    print("")


def write_temp_file(
    input_data="",
    suffix=None,
    prefix=None,
    dir=None,
):
    """
    Cria um arquivo temporário com os dados de entrada fornecidos.

    :param input_data: Conteúdo a ser gravado no arquivo temporário
    :param suffix: Extensão opcional do arquivo (sem o ponto)
    :param prefix: Prefixo opcional para o nome do arquivo temporário
    :param dir: Diretório opcional no qual criar o arquivo
    :return: Caminho para o arquivo temporário criado
    :raises: OSError se a criação ou gravação do arquivo falhar
    """
    kwargs = {"prefix": prefix, "dir": dir}
    if suffix:
        kwargs["suffix"] = f".{suffix}"
    fd, filepath = tempfile.mkstemp(**kwargs)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(input_data)
    except Exception:
        os.close(fd)
        raise
    return filepath


def get_environment_editor(default=None):
    """
    Obtém o editor preferido a partir das variáveis de ambiente.

    Esta função verifica as seguintes variáveis de ambiente, nesta ordem, para
    determinar o editor preferido do usuário:

     - VISUAL
     - EDITOR

    :param default: Editor padrão retornado quando nenhuma variável de ambiente está definida.
    :type default: str ou None
    :return: Editor preferido conforme definido pelas variáveis de ambiente ou o valor padrão.
    :rtype: str ou None
    """
    editor = os.environ.get("VISUAL", os.environ.get("EDITOR", default))
    return editor


def discover_editor(editor_override=None):
    """
    Descobre e retorna o comando de editor apropriado.

    Lida com casos em que o comando do editor inclui argumentos, inclusive argumentos entre aspas
    que contêm espaços (por exemplo, 'vim -c "set noswapfile"').

    :return: Comando do editor como string
    :rtype: str
    """
    system = platform.system()
    if system == "Windows":
        default_editor = DEFAULT_EDITOR_WINDOWS
    elif system == "Darwin":
        default_editor = DEFAULT_EDITOR_OS_X
    else:
        default_editor = DEFAULT_EDITOR_NIX

    if editor_override:
        editor = editor_override
    else:
        editor = get_environment_editor(default_editor)

    return editor


def pipe_editor(input_data="", suffix=None, editor=None):
    """
    Abre o editor do sistema com dados de entrada opcionais e retorna o conteúdo editado.

    Esta função cria um arquivo temporário com os dados de entrada fornecidos, abre esse arquivo
    no editor do sistema, aguarda o usuário fazer as alterações e fechar o editor e, em seguida,
    lê e retorna o conteúdo modificado. O arquivo temporário é excluído depois.

    :param input_data: Conteúdo inicial usado para preencher o editor
    :type input_data: str
    :param suffix: Extensão opcional do arquivo temporário (por exemplo, '.txt', '.md')
    :type suffix: str ou None
    :return: Conteúdo editado após o fechamento do editor
    :rtype: str
    """
    filepath = write_temp_file(input_data, suffix)
    command_str = discover_editor(editor)
    command_str += " " + filepath

    subprocess.call(command_str, shell=True)
    with open(filepath, "r") as f:
        output_data = f.read()
    try:
        os.remove(filepath)
    except PermissionError:
        print_status_message(
            False,
            (
                f"AVISO: não foi possível excluir o arquivo temporário {filepath!r}. Talvez seja necessário excluí-lo"
                " manualmente."
            ),
        )
    return output_data
