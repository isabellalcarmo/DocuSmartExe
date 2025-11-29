# **DocuSmart**

> **Organizador inteligente de documentos com IA Híbrida (Local + Cloud)**

Aplicação desktop para classificação e organização automática de arquivos. Utiliza uma abordagem híbrida: modelo local SBERT para triagem rápida/offline e Google Gemini (via Supabase Edge Functions) para análise semântica profunda. Interface construída em CustomTkinter.

## Visão Geral
- **Frontend/Desktop:** Python 3.10+ com CustomTkinter (GUI) e multithreading para não congelar a interface.
- **Backend:** Supabase (Auth para login, Database para perfis, Edge Functions para lógica serverless).
- **IA Local:** `sentence-transformers` (SBERT) + Regex para classificação sem custos.
- **IA Cloud:** Google Gemini 2.0 Flash (via Edge Functions em Deno/TypeScript) para alta precisão.
- **OCR:** Integração com Tesseract e Poppler para extração de texto em imagens e PDFs escaneados.
- **Persistência Local:** Cache JSON (`cache_{user_id}.json`) para evitar reprocessamento de arquivos conhecidos.

## Estrutura do Projeto
```bash
docusmart/
├── docusmart_app.py              # Entry point da GUI, login e controle de threads
├── organizer.py                  # Lógica de negócio (OCR, Classificação, API, Cache)
├── config.py                     # Gerenciamento de envs, conexão Supabase e Singleton
├── fix_asyncio.py                # Patch de compatibilidade de Event Loop para Windows
├── requirements.txt              # Dependências Python (pip)
├── DocuSmartApp.spec             # Especificação para build do executável (PyInstaller)
├── robot-head.ico                # Ícone da aplicação

├── tesseract/                    # Binários portáteis do Tesseract OCR

├── poppler-24.08.0/              # Binários do Poppler usados para extrair texto de PDFs

└── supabase/
    └── functions/                # Código das Edge Functions (TypeScript)
        ├── classify-document-file/         # Função para upload de arquivos (Base64)
        ├── classify-document-gemini/       # Função para processamento de texto puro
        └── generate-category-description/  # Função para gerar descrição de categoria

```

## Pré-requisitos

Para executar o projeto a partir do código fonte (modo desenvolvedor), você precisará de:

- Python 3.10 ou superior.
- Tesseract OCR instalado e adicionado ao PATH do sistema.
- Poppler (para manipulação de PDF) instalado e adicionado ao PATH.
- Conta no Supabase (para as chaves de API).

## Setup de Desenvolvimento

1. Configurar Ambiente Python

```bash
# Criar virtual environment
python -m venv venv

# Ativar virtual environment
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Instalar dependências do projeto
pip install -r requirements.txt
```

2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (mesmo nível de `config.py`) com as suas credenciais do Supabase. O sistema usa a biblioteca python-dotenv para ler este arquivo.

```bash
SUPABASE_URL="sua_url_do_projeto_supabase"
SUPABASE_KEY="sua_anon_key_publica"
```

> **Nota Importante**: A chave da API do Google Gemini NÃO deve ser colocada aqui. Ela deve ser configurada nos Secrets do seu projeto Supabase (Dashboard > Project Settings > Edge Functions > Secrets) com o nome GEMINI_API_KEY_EDGE.

3. Executar a Aplicação

```bash
# Iniciar a interface gráfica
python docusmart_app.py
```

## Configuração e Dependências Externas (OCR)

O módulo `organizer.py` tenta localizar as ferramentas de OCR automaticamente. Se você encontrar erros como "OCR não encontrado" ou falha ao processar imagens, verifique:

1. Tesseract: O código busca o executável no PATH do sistema ou, se estiver rodando o executável compilado, na pasta interna `/_internal/tesseract/`.
2. Poppler: O código busca os binários na pasta local `/_internal/poppler/bin` ou no PATH.

Desenvolvedores: Se suas instalações estiverem em diretórios não padronizados, edite as funções `get_tesseract_path()` e `get_poppler_path()` em `organizer.py`.

## Build (Gerar Executável)

Para gerar o arquivo `.exe` para distribuição (Windows), utilize o PyInstaller com o arquivo de especificação incluído, que já trata das dependências ocultas e ícones.

```bash
# Gera o executável na pasta dist/
pyinstaller DocuSmartApp.spec
```

## Testes e Logs

**Logs de Execução**: A aplicação exibe logs detalhados na caixa de texto à direita da interface gráfica.

**Limpeza de Cache**: Para forçar o reprocessamento de arquivos e testar a IA novamente, apague os arquivos .json gerados na pasta de dados do aplicativo:

- Windows: `%APPDATA%\DocuSmart`
- Mac/Linux: `~/.config/DocuSmart`