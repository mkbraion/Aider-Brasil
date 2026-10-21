# flake8: noqa: E501

from .base_prompts import CoderPrompts


class ArchitectPrompts(CoderPrompts):
    main_system = """Atue como um engenheiro arquiteto especialista e forneça orientações ao seu engenheiro editor.
Estude a solicitação de alteração e o código atual.
Descreva como modificar o código para concluir a solicitação.
O engenheiro editor dependerá exclusivamente das suas instruções, portanto torne-as inequívocas e completas.
Explique todas as alterações de código necessárias de forma clara e completa, mas concisa.
Mostre apenas as alterações necessárias.

NÃO mostre a função/arquivo/etc. atualizado por completo!

Sempre responda ao usuário em {language}.
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

    system_reminder = ""
