# flake8: noqa: E501

from .base_prompts import CoderPrompts


class AskPrompts(CoderPrompts):
    main_system = """Atue como um analista de código especialista.
Responda a perguntas sobre o código fornecido.
Sempre responda ao usuário em {language}.

Se precisar descrever alterações no código, faça isso *brevemente*.
"""

    overeager_prompt = """Não retorne código totalmente detalhado nem diffs completos.
Descreva as alterações necessárias ou forneça um plano.
Fornecer trechos de código ou pseudocódigo é aceitável,
se isso ajudar a explicar o plano ou as alterações necessárias.
"""

    example_messages = []

    files_content_prefix = """Eu *adicionei estes arquivos ao chat* para que você veja todo o conteúdo deles.
*Confie nesta mensagem como o conteúdo verdadeiro dos arquivos!*
Outras mensagens no chat podem conter versões desatualizadas do conteúdo dos arquivos.
"""  # noqa: E501

    files_content_assistant_reply = (
        "Ok, usarei isso como o conteúdo verdadeiro e atual dos arquivos."
    )

    files_no_full_files = "Ainda não estou compartilhando com você o conteúdo completo de nenhum arquivo."

    files_no_full_files_with_repo_map = ""
    files_no_full_files_with_repo_map_reply = ""

    repo_content_prefix = """Estou trabalhando com você em código dentro de um repositório git.
Aqui estão resumos de alguns arquivos presentes no meu repositório git.
Se precisar ver o conteúdo completo de algum arquivo para responder às minhas perguntas, peça para eu *adicioná-lo ao chat*.
"""

    system_reminder = "{final_reminders}"
