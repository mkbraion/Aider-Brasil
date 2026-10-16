import json
import platform
import sys
import time
import uuid
from pathlib import Path

from mixpanel import MixpanelException
from posthog import Posthog

from aider import __version__
from aider.dump import dump  # noqa: F401
from aider.models import model_info_manager

PERCENT = 10


def compute_hex_threshold(percent):
    """Converte uma porcentagem em um limite hexadecimal de 6 dígitos.

    Args:
        percent: Limite percentual (0-100)

    Returns:
        str: Limite hexadecimal de 6 dígitos
    """
    return format(int(0xFFFFFF * percent / 100), "06x")


def is_uuid_in_percentage(uuid_str, percent):
    """Verifica se uma UUID está dentro dos primeiros X por cento do espaço de UUIDs.

    Args:
        uuid_str: UUID a ser verificada
        percent: Limite percentual (0-100)

    Returns:
        bool: True se a UUID estiver dentro dos primeiros X por cento
    """
    if not (0 <= percent <= 100):
        raise ValueError("A porcentagem deve estar entre 0 e 100")

    if not uuid_str:
        return False

    # Converte a porcentagem em um limite hexadecimal (1% = "04...", 10% = "1a...", etc.)
    # Usa os 6 primeiros dígitos hexadecimais
    if percent == 0:
        return False

    threshold = compute_hex_threshold(percent)
    return uuid_str[:6] <= threshold


mixpanel_project_token = "6da9a43058a5d1b9f3353153921fb04d"
posthog_project_api_key = "phc_99T7muzafUMMZX15H8XePbMSreEUzahHbtWjy3l5Qbv"
posthog_host = "https://us.i.posthog.com"


class Analytics:
    # provedores
    mp = None
    ph = None

    # dados salvos
    user_id = None
    permanently_disable = None
    asked_opt_in = None

    # dados temporários da sessão
    logfile = None

    def __init__(
        self,
        logfile=None,
        permanently_disable=False,
        posthog_host=None,
        posthog_project_api_key=None,
    ):
        self.logfile = logfile
        self.get_or_create_uuid()
        self.custom_posthog_host = posthog_host
        self.custom_posthog_project_api_key = posthog_project_api_key

        if self.permanently_disable or permanently_disable or not self.asked_opt_in:
            self.disable(permanently_disable)

    def enable(self):
        if not self.user_id:
            self.disable(False)
            return

        if self.permanently_disable:
            self.disable(True)
            return

        if not self.asked_opt_in:
            self.disable(False)
            return

        # self.mp = Mixpanel(mixpanel_project_token)
        self.ph = Posthog(
            project_api_key=self.custom_posthog_project_api_key or posthog_project_api_key,
            host=self.custom_posthog_host or posthog_host,
            on_error=self.posthog_error,
            enable_exception_autocapture=True,
            super_properties=self.get_system_info(),  # Adiciona informações do sistema a todos os eventos
        )

    def disable(self, permanently):
        self.mp = None
        self.ph = None

        if permanently:
            self.asked_opt_in = True
            self.permanently_disable = True
            self.save_data()

    def need_to_ask(self, args_analytics):
        if args_analytics is False:
            return False

        could_ask = not self.asked_opt_in and not self.permanently_disable
        if not could_ask:
            return False

        if args_analytics is True:
            return True

        assert args_analytics is None, args_analytics

        if not self.user_id:
            return False

        return is_uuid_in_percentage(self.user_id, PERCENT)

    def get_data_file_path(self):
        try:
            data_file = Path.home() / ".aider" / "analytics.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            return data_file
        except OSError:
            # Se não for possível criar ou acessar o diretório, apenas desativa a telemetria
            self.disable(permanently=False)
            return None

    def get_or_create_uuid(self):
        self.load_data()
        if self.user_id:
            return

        self.user_id = str(uuid.uuid4())
        self.save_data()

    def load_data(self):
        data_file = self.get_data_file_path()
        if not data_file:
            return

        if data_file.exists():
            try:
                data = json.loads(data_file.read_text())
                self.permanently_disable = data.get("permanently_disable")
                self.user_id = data.get("uuid")
                self.asked_opt_in = data.get("asked_opt_in", False)
            except (json.decoder.JSONDecodeError, OSError):
                self.disable(permanently=False)

    def save_data(self):
        data_file = self.get_data_file_path()
        if not data_file:
            return

        data = dict(
            uuid=self.user_id,
            permanently_disable=self.permanently_disable,
            asked_opt_in=self.asked_opt_in,
        )

        try:
            data_file.write_text(json.dumps(data, indent=4))
        except OSError:
            # Se não for possível gravar o arquivo, apenas desativa a telemetria
            self.disable(permanently=False)

    def get_system_info(self):
        return {
            "python_version": sys.version.split()[0],
            "os_platform": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "aider_version": __version__,
        }

    def _redact_model_name(self, model):
        if not model:
            return None

        info = model_info_manager.get_model_from_cached_json_db(model.name)
        if info:
            return model.name
        elif "/" in model.name:
            return model.name.split("/")[0] + "/REDACTED"
        return None

    def posthog_error(self):
        """Desativa o PostHog caso ocorra um erro."""
        print("X" * 100)
        # https://github.com/PostHog/posthog-python/blob/9e1bb8c58afaa229da24c4fb576c08bb88a75752/posthog/consumer.py#L86
        # https://github.com/Aider-AI/aider/issues/2532
        self.ph = None

    def event(self, event_name, main_model=None, **kwargs):
        if not self.mp and not self.ph and not self.logfile:
            return

        properties = {}

        if main_model:
            properties["main_model"] = self._redact_model_name(main_model)
            properties["weak_model"] = self._redact_model_name(main_model.weak_model)
            properties["editor_model"] = self._redact_model_name(main_model.editor_model)

        properties.update(kwargs)

        # Mantém valores numéricos como números
        for key, value in properties.items():
            if isinstance(value, (int, float)):
                properties[key] = value
            else:
                properties[key] = str(value)

        if self.mp:
            try:
                self.mp.track(self.user_id, event_name, dict(properties))
            except MixpanelException:
                self.mp = None  # Desativa o Mixpanel em caso de erro de conexão

        if self.ph:
            self.ph.capture(event_name, distinct_id=self.user_id, properties=dict(properties))

        if self.logfile:
            log_entry = {
                "event": event_name,
                "properties": properties,
                "user_id": self.user_id,
                "time": int(time.time()),
            }
            try:
                with open(self.logfile, "a") as f:
                    json.dump(log_entry, f)
                    f.write("\n")
            except OSError:
                pass  # Ignora erros do sistema operacional ao gravar o arquivo de log


if __name__ == "__main__":
    dump(compute_hex_threshold(PERCENT))
