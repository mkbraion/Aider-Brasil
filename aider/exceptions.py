from dataclasses import dataclass

from aider.dump import dump  # noqa: F401


@dataclass
class ExInfo:
    name: str
    retry: bool
    description: str


EXCEPTIONS = [
    ExInfo("APIConnectionError", True, None),
    ExInfo("APIError", True, None),
    ExInfo("APIResponseValidationError", True, None),
    ExInfo(
        "AuthenticationError",
        False,
        "O provedor da API não conseguiu autenticar você. Verifique sua chave de API.",
    ),
    ExInfo("AzureOpenAIError", True, None),
    ExInfo("BadGatewayError", True, "Os servidores do provedor da API estão indisponíveis ou sobrecarregados."),
    ExInfo("BadRequestError", False, None),
    ExInfo("BudgetExceededError", True, None),
    ExInfo(
        "ContentPolicyViolationError",
        True,
        "O provedor da API recusou a solicitação devido a uma política de segurança relacionada ao conteúdo.",
    ),
    ExInfo("ContextWindowExceededError", False, None),  # caso especial tratado em base_coder
    ExInfo("ImageFetchError", False, "O provedor da API não conseguiu buscar uma ou mais imagens."),
    ExInfo("InternalServerError", True, "Os servidores do provedor da API estão indisponíveis ou sobrecarregados."),
    ExInfo("InvalidRequestError", True, None),
    ExInfo("JSONSchemaValidationError", True, None),
    ExInfo("NotFoundError", False, None),
    ExInfo(
        "PermissionDeniedError",
        False,
        "A permissão foi negada. Verifique sua chave de API e/ou suas credenciais.",
    ),
    ExInfo("OpenAIError", True, None),
    ExInfo(
        "RateLimitError",
        True,
        "O provedor da API aplicou um limite de requisições. Tente novamente mais tarde ou verifique suas cotas.",
    ),
    ExInfo("RouterRateLimitError", True, None),
    ExInfo("ServiceUnavailableError", True, "Os servidores do provedor da API estão indisponíveis ou sobrecarregados."),
    ExInfo("UnprocessableEntityError", True, None),
    ExInfo("UnsupportedParamsError", True, None),
    ExInfo(
        "Timeout",
        True,
        "O provedor da API excedeu o tempo limite sem retornar uma resposta. Ele pode estar indisponível ou sobrecarregado.",
    ),
]


class LiteLLMExceptions:
    exceptions = dict()
    exception_info = {exi.name: exi for exi in EXCEPTIONS}

    def __init__(self):
        self._load()

    def _load(self, strict=False):
        import litellm

        for var in dir(litellm):
            # Filtra por BaseException porque instâncias de classes que não são exceções não podem ser capturadas.
            # `litellm.ErrorEventError` é um exemplo de classe comum cujo nome apenas termina
            # com `Error`.
            if var.endswith("Error") and issubclass(getattr(litellm, var), BaseException):
                if var not in self.exception_info:
                    raise ValueError(f"{var} existe no litellm, mas não está na lista de exceções do aider")

        for var in self.exception_info:
            ex = getattr(litellm, var)
            self.exceptions[ex] = self.exception_info[var]

    def exceptions_tuple(self):
        return tuple(self.exceptions)

    def get_ex_info(self, ex):
        """Retorna o ExInfo correspondente a uma determinada instância de exceção."""
        import litellm

        if ex.__class__ is litellm.APIConnectionError:
            if "boto3" in str(ex):
                return ExInfo("APIConnectionError", False, "Você precisa executar: pip install boto3")
            if "OpenrouterException" in str(ex) and "'choices'" in str(ex):
                return ExInfo(
                    "APIConnectionError",
                    True,
                    (
                        "O OpenRouter ou o provedor de API upstream está indisponível, sobrecarregado ou"
                        " limitando a taxa das suas solicitações."
                    ),
                )

        # Verifica casos específicos de APIError que não devem ser repetidos, como créditos insuficientes
        if ex.__class__ is litellm.APIError:
            err_str = str(ex).lower()
            if "insufficient credits" in err_str and '"code":402' in err_str:
                return ExInfo(
                    "APIError",
                    False,
                    "Créditos insuficientes no provedor da API. Adicione créditos para continuar.",
                )
            # Segue para o tratamento padrão de APIError quando não for o caso específico de créditos

        return self.exceptions.get(ex.__class__, ExInfo(None, None, None))
