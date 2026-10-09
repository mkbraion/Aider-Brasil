<div align="center">

# 🇧🇷 Aider Brasil

### Programação em par com IA direto no terminal — versão em português do Brasil

**Tradução, adaptação brasileira e manutenção por [MKBraion (@mkbraion)](https://github.com/mkbraion).**

[![GitHub Stars](https://img.shields.io/github/stars/mkbraion/Aider-Brasil?style=flat-square&logo=github&label=Estrelas)](https://github.com/mkbraion/Aider-Brasil/stargazers)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-Apache%202.0-blue?style=flat-square)](LICENSE.txt)
[![Brasil](https://img.shields.io/badge/idioma-Portugu%C3%AAs%20do%20Brasil-009739?style=flat-square)](#)

**[Instalação](#-instalação-rápida) · [Como usar](#-como-usar) · [Recursos](#-principais-recursos) · [Modelos](#-modelos-de-ia) · [Git](#-integração-com-git) · [FAQ](#-perguntas-frequentes)**

</div>

---

## 🇧🇷 Sobre o Aider Brasil

O **Aider Brasil** é uma adaptação em português brasileiro do Aider, preparada para tornar a ferramenta mais acessível para desenvolvedores, estudantes e profissionais de tecnologia no Brasil.

Com ele, você conversa com uma IA diretamente no terminal e pode pedir para ela:

- criar funcionalidades;
- corrigir bugs;
- refatorar código;
- explicar arquivos e funções;
- gerar testes;
- alterar vários arquivos de uma vez;
- analisar seu repositório inteiro;
- trabalhar com Git automaticamente;
- utilizar modelos da OpenAI, Anthropic, DeepSeek e outros provedores.

A proposta desta versão é deixar a apresentação, documentação principal e experiência de aprendizado mais claras para o público brasileiro.

> **Responsável pela versão brasileira:** Nelson Neto — **MKBraion / @mkbraion**  
> Tradução, adaptação de conteúdo, organização e manutenção da edição brasileira.

---

## 🚀 Instalação rápida

O Aider utiliza Python. No Windows, Linux ou macOS, abra o terminal e execute:

```bash
python -m pip install aider-install
aider-install
```

Depois entre na pasta do seu projeto:

```bash
cd caminho/do/seu/projeto
```

Exemplo no Windows:

```powershell
cd "C:\Users\SeuUsuario\Documents\meu-projeto"
```

Agora inicie o Aider com o modelo desejado.

### OpenAI

```bash
aider --model o3-mini --api-key openai=SUA_CHAVE
```

### Anthropic / Claude

```bash
aider --model sonnet --api-key anthropic=SUA_CHAVE
```

### DeepSeek

```bash
aider --model deepseek --api-key deepseek=SUA_CHAVE
```

> Nunca publique suas chaves de API no GitHub. Prefira variáveis de ambiente ou arquivos de configuração ignorados pelo Git.

---

## 💻 Como usar

Dentro de qualquer repositório local, execute:

```bash
aider
```

Depois converse normalmente com a IA.

Exemplos:

```text
Analise este projeto e me explique como ele está organizado.
```

```text
Crie uma tela de login com validação e integração com a API existente.
```

```text
Encontre o erro que está causando falha neste módulo e corrija.
```

```text
Refatore este código sem alterar o comportamento atual.
```

```text
Crie testes para as funções que ainda não possuem cobertura.
```

O Aider lê o contexto do projeto e aplica alterações diretamente nos arquivos.

---

## ✨ Principais recursos

### 🧠 Modelos locais e na nuvem

Pode ser conectado a diferentes modelos de linguagem, incluindo provedores comerciais e modelos executados localmente.

### 🗺️ Mapa do código do projeto

O Aider cria uma visão estrutural do seu repositório para compreender relações entre arquivos, classes, funções e dependências.

Isso ajuda principalmente em projetos grandes, onde seria inviável enviar todos os arquivos ao modelo em cada mensagem.

### 💻 Mais de 100 linguagens

Funciona com várias linguagens e formatos, incluindo:

- Python
- JavaScript
- TypeScript
- Java
- C
- C++
- C#
- Go
- Rust
- Ruby
- PHP
- HTML
- CSS
- SQL
- Shell
- e muitas outras.

### 🌿 Integração com Git

Uma das funções mais úteis é a integração automática com Git.

Depois de realizar alterações, o Aider pode criar commits com mensagens coerentes, facilitando:

- revisão das mudanças;
- comparação de versões;
- reversão de alterações;
- trabalho em branches;
- controle do histórico.

### 🖥️ Uso junto com IDEs

Você pode usar o Aider enquanto trabalha no VS Code, Cursor, JetBrains ou outro editor.

A IA atua sobre os mesmos arquivos que você está editando localmente.

### 🖼️ Imagens e páginas web

Também é possível fornecer imagens, capturas de tela, páginas da web e documentação como contexto para determinadas tarefas.

### 🎙️ Voz para código

O projeto oferece fluxo de voz para código, permitindo ditar instruções e solicitar implementações usando fala.

### ✅ Testes e lint

O Aider pode executar ferramentas de lint e testes depois das alterações e tentar corrigir problemas detectados automaticamente.

---

## 🤖 Modelos de IA

O Aider pode trabalhar com diversos provedores.

A disponibilidade dos modelos muda com o tempo, portanto os nomes abaixo são apenas exemplos de configuração.

### OpenAI

```bash
aider --model o3-mini
```

### Claude

```bash
aider --model sonnet
```

### DeepSeek

```bash
aider --model deepseek
```

Além deles, o Aider suporta diversos modelos compatíveis por meio de provedores e APIs adicionais.

---

## 🌿 Integração com Git

O fluxo recomendado é iniciar o Aider dentro de um repositório Git.

Exemplo:

```bash
git init
aider
```

Você pode então pedir:

```text
Adicione autenticação JWT e faça um commit das alterações.
```

O histórico do Git permite revisar exatamente o que a IA modificou.

Comandos úteis:

```bash
git status
git diff
git log --oneline
```

Para desfazer uma alteração, utilize os recursos normais do Git de acordo com o estado do seu repositório.

---

## 🪟 Uso no Windows

Para usuários brasileiros no Windows, recomendamos:

1. instalar Python;
2. instalar Git for Windows;
3. utilizar PowerShell ou Windows Terminal;
4. instalar o Aider;
5. entrar na pasta do projeto;
6. iniciar o Aider.

Exemplo:

```powershell
python --version
git --version
python -m pip install aider-install
aider-install
cd "C:\Projetos\meu-app"
aider
```

---

## 🔐 Configuração de chaves de API

Evite colocar a chave diretamente em arquivos enviados ao GitHub.

No PowerShell, por exemplo:

```powershell
$env:OPENAI_API_KEY="sua-chave"
```

ou:

```powershell
$env:ANTHROPIC_API_KEY="sua-chave"
```

Depois inicie o Aider normalmente.

---

## 🧩 Exemplo de fluxo completo

```powershell
cd "C:\Projetos\minha-api"

git status

aider --model sonnet
```

Dentro do Aider:

```text
Analise a arquitetura atual da API.
```

Depois:

```text
Crie um endpoint de cadastro seguindo a estrutura existente.
```

E então:

```text
Crie testes para esse endpoint e corrija qualquer falha encontrada.
```

Ao final, confira:

```bash
git status
git log --oneline
```

---

## 👨‍💻 Para quem esta versão é indicada?

O Aider Brasil é especialmente útil para:

- quem está aprendendo programação;
- desenvolvedores brasileiros que preferem documentação em português;
- estudantes de Ciência da Computação, Engenharia de Software, Sistemas de Informação e áreas relacionadas;
- profissionais que trabalham com projetos grandes;
- quem deseja utilizar IA dentro do terminal;
- equipes que querem experimentar desenvolvimento assistido por modelos de linguagem.

---

## ❓ Perguntas frequentes

### O Aider é uma IDE?

Não. Ele funciona principalmente como uma ferramenta de programação assistida por IA no terminal e pode ser utilizada junto com sua IDE favorita.

### Ele altera os arquivos sozinho?

Sim, quando você aprova ou utiliza os fluxos correspondentes. Por isso, é recomendado trabalhar com Git.

### Posso usar em projetos existentes?

Sim. Esse é um dos principais usos da ferramenta.

### Funciona em português?

Você pode conversar com os modelos em português. Esta edição do repositório também tem como objetivo adaptar a documentação e a apresentação para **português brasileiro**.

### Preciso pagar?

O código da ferramenta é aberto, mas muitos modelos de IA utilizados por API possuem cobrança própria do provedor.

### Funciona com modelos locais?

Sim, dependendo do modelo, servidor e integração utilizada.

---

## 🤝 Contribuindo com a versão brasileira

Contribuições para melhorar a tradução e a experiência brasileira são bem-vindas.

Você pode:

- corrigir traduções;
- melhorar exemplos para Windows/Linux usados no Brasil;
- adicionar tutoriais;
- documentar problemas comuns;
- melhorar mensagens e textos em português;
- propor melhorias por Issues e Pull Requests.

Repositório da versão brasileira:

**https://github.com/mkbraion/Aider-Brasil**

---

## 🇧🇷 Responsável pela adaptação brasileira

**Nelson Neto — MKBraion**  
GitHub: [@mkbraion](https://github.com/mkbraion)

Responsável pela tradução, adaptação, organização e manutenção desta versão destinada ao público brasileiro.

---

## 📜 Licença e créditos do projeto-base

Esta distribuição brasileira é baseada no projeto Aider e mantém os avisos e termos de licença exigidos pelo software de origem.

O código-base é distribuído sob a **Apache License 2.0**. O texto integral permanece disponível em [`LICENSE.txt`](LICENSE.txt).

A versão brasileira, sua tradução, documentação e adaptações são mantidas por **Nelson Neto / MKBraion (@mkbraion)**.

Créditos e referências ao projeto-base são preservados nesta seção e nos arquivos de licenciamento necessários para atender às condições da licença aplicável.
