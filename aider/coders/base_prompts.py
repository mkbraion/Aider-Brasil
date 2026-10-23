class CoderPrompts:
    system_reminder = ""

    files_content_gpt_edits = "Confirmei as alterações com o hash git {hash} e a mensagem de commit: {message}"

    files_content_gpt_edits_no_repo = "Atualizei os arquivos."

    files_content_gpt_no_edits = "Não encontrei nenhuma edição formatada corretamente na sua resposta?!"

    files_content_local_edits = "Eu mesmo editei os arquivos."

    lazy_prompt = """Você é diligente e incansável!
Você NUNCA deixa comentários descrevendo código sem implementá-lo!
Você sempre IMPLEMENTA COMPLETAMENTE o código necessário!
"""

    overeager_prompt = """Preste muita atenção ao escopo da solicitação do usuário.
Faça o que ele pedir, mas nada além disso.
Não melhore, comente, corrija ou modifique de forma alguma partes não relacionadas do código!
"""

    example_messages = []

    files_content_prefix = """Eu *adicionei estes arquivos ao chat* para que você possa editá-los.

*Considere esta mensagem como o conteúdo verdadeiro destes arquivos!*
Outras mensagens no chat podem conter versões desatualizadas do conteúdo dos arquivos.
"""  # noqa: E501

    files_content_assistant_reply = "Certo, qualquer alteração que eu propuser será nesses arquivos."

    files_no_full_files = "Ainda não estou compartilhando nenhum arquivo que você possa editar."

    files_no_full_files_with_repo_map = """Não tente editar nenhum código existente sem me pedir para adicionar os arquivos ao chat!
Diga quais arquivos do meu repositório têm maior probabilidade de **precisar de alterações** para resolver as solicitações que eu fizer e então pare para que eu possa adicioná-los ao chat.
Inclua apenas os arquivos que realmente têm maior probabilidade de precisar ser editados.
Não inclua arquivos que possam apenas conter contexto relevante; inclua somente arquivos que precisarão ser alterados.
"""  # noqa: E501

    files_no_full_files_with_repo_map_reply = (
        "Certo, com base nas suas solicitações, vou sugerir quais arquivos precisam ser editados e então"
        " vou parar e aguardar sua aprovação."
    )

    repo_content_prefix = """Aqui estão resumos de alguns arquivos presentes no meu repositório git.
Não proponha alterações nesses arquivos; trate-os como *somente leitura*.
Se precisar editar algum desses arquivos, peça primeiro para eu *adicioná-lo ao chat*.
"""

    read_only_files_prefix = """Aqui estão alguns arquivos SOMENTE LEITURA, fornecidos para sua referência.
Não edite estes arquivos!
"""

    shell_cmd_prompt = ""
    shell_cmd_reminder = ""
    no_shell_cmd_prompt = ""
    no_shell_cmd_reminder = ""

    rename_with_shell = ""
    go_ahead_tip = ""
