def scrub_sensitive_info(args, text):
    # Substitui informações sensíveis pelos 4 últimos caracteres
    if text and args.openai_api_key:
        last_4 = args.openai_api_key[-4:]
        text = text.replace(args.openai_api_key, f"...{last_4}")
    if text and args.anthropic_api_key:
        last_4 = args.anthropic_api_key[-4:]
        text = text.replace(args.anthropic_api_key, f"...{last_4}")
    return text


def format_settings(parser, args):
    show = scrub_sensitive_info(args, parser.format_values())
    # Organiza e traduz os cabeçalhos mantendo compatibilidade com a saída do configargparse
    heading_env = "Environment Variables:"
    heading_defaults = "Defaults:"
    if heading_env in show:
        show = show.replace(heading_env, "\nVariáveis de ambiente:")
        show = show.replace(heading_defaults, "\nValores padrão:")
    show += "\n"
    show += "Configurações das opções:\n"
    for arg, val in sorted(vars(args).items()):
        if val:
            val = scrub_sensitive_info(args, str(val))
        show += f"  - {arg}: {val}\n"  # noqa: E221
    return show
