import os
import sys
import time
from pathlib import Path

import packaging.version

import aider
from aider import utils
from aider.dump import dump  # noqa: F401

VERSION_CHECK_FNAME = Path.home() / ".aider" / "caches" / "versioncheck"


def install_from_main_branch(io):
    """
    Instala a versão mais recente do aider a partir da branch main do repositório GitHub.
    """

    return utils.check_pip_install_extra(
        io,
        None,
        "Instalar a versão de desenvolvimento do aider a partir da branch main?",
        ["git+https://github.com/Aider-AI/aider.git"],
        self_update=True,
    )


def install_upgrade(io, latest_version=None):
    """
    Instala a versão mais recente do aider a partir do PyPI.
    """

    if latest_version:
        new_ver_text = f"Uma versão mais recente do aider, v{latest_version}, está disponível."
    else:
        new_ver_text = "Instalar a versão mais recente do aider?"

    docker_image = os.environ.get("AIDER_DOCKER_IMAGE")
    if docker_image:
        text = f"""
{new_ver_text} Para atualizar, execute:

    docker pull {docker_image}
"""
        io.tool_warning(text)
        return True

    success = utils.check_pip_install_extra(
        io,
        None,
        new_ver_text,
        ["aider-chat"],
        self_update=True,
    )

    if success:
        io.tool_output("Execute o aider novamente para usar a nova versão.")
        sys.exit()

    return


def check_version(io, just_check=False, verbose=False):
    if not just_check and VERSION_CHECK_FNAME.exists():
        day = 60 * 60 * 24
        since = time.time() - os.path.getmtime(VERSION_CHECK_FNAME)
        if 0 < since < day:
            if verbose:
                hours = since / 60 / 60
                io.tool_output(f"Ainda é cedo para verificar a versão: {hours:.1f} horas")
            return

    # Para manter a inicialização rápida, evita importar isto até que seja necessário
    import requests

    try:
        response = requests.get("https://pypi.org/pypi/aider-chat/json")
        data = response.json()
        latest_version = data["info"]["version"]
        current_version = aider.__version__

        if just_check or verbose:
            io.tool_output(f"Versão atual: {current_version}")
            io.tool_output(f"Versão mais recente: {latest_version}")

        is_update_available = packaging.version.parse(latest_version) > packaging.version.parse(
            current_version
        )
    except Exception as err:
        io.tool_error(f"Erro ao verificar uma nova versão no PyPI: {err}")
        return False
    finally:
        VERSION_CHECK_FNAME.parent.mkdir(parents=True, exist_ok=True)
        VERSION_CHECK_FNAME.touch()

    ###
    # is_update_available = True

    if just_check or verbose:
        if is_update_available:
            io.tool_output("Atualização disponível")
        else:
            io.tool_output("Nenhuma atualização disponível")

    if just_check:
        return is_update_available

    if not is_update_available:
        return False

    install_upgrade(io, latest_version)
    return True
