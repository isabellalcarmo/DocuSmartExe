# **DocuSmart**

> **Organizador Inteligente de Documentos com IA Híbrida (Local + Cloud)**

Aplicação desktop para classificação e organização automática de arquivos digitais. O DocuSmart combina privacidade e eficiência através de uma arquitetura híbrida: utiliza o modelo **SBERT** localmente para triagem rápida e sem custos, e integra o **Google Gemini** (via Supabase Edge Functions) para análises semânticas complexas na nuvem.

---

## 🚀 Visão Geral da Arquitetura

* **Frontend:** Python 3.10+ com **CustomTkinter** (Interface Moderna) e gerenciamento de *threads* para responsividade.
* **Backend:** **Supabase** (Auth, Database e Edge Functions).
* **IA Local (Offline):** `sentence-transformers` (SBERT) + Regex.
* **IA Cloud (Online):** Google Gemini 2.0 Flash executado em ambiente serverless (Deno/TypeScript).
* **OCR & Parsing:** Integração nativa com **Tesseract** e **Poppler** para leitura de imagens e PDFs escaneados.
* **Performance:** Sistema de cache local JSON (`cache_{user_id}.json`) para evitar reprocessamento redundante.

---

## 📂 Estrutura do Projeto

```bash
docusmart/
├── docusmart_app.py              # Ponto de entrada (GUI, Login, Threads)
├── organizer.py                  # Motor lógico (OCR, Classificação, API, Cache)
├── config.py                     # Configuração de ambiente e Singleton do Supabase
├── fix_asyncio.py                # Patch de compatibilidade (Event Loop Windows)
├── requirements.txt              # Dependências do Python
├── DocuSmartApp.spec             # Script de build (PyInstaller)
├── robot-head.ico                # Assets gráficos
│
├── tesseract/                    # Binários portáteis do OCR
├── poppler-24.08.0/              # Binários para manipulação de PDF
│
├── modelos/                      # [GitIgnored] Pesos do modelo SBERT (Ver seção abaixo)
│
└── supabase/
    └── functions/                # Serverless Edge Functions (TypeScript)
        ├── classify-document-file/       # Upload e análise de arquivos
        ├── classify-document-gemini/     # Análise de texto puro
        └── generate-category-description/# Auxiliar de UX
```

## ⚠️ Configuração Crítica: Modelos de IA Local

Devido ao tamanho dos arquivos de pesos neurais, a pasta `modelos/` não está incluída no repositório. Portanto, para que a aplicação funcione, você deve baixar o modelo SBERT manualmente.

**Passo a passo**:

1. Crie um arquivo chamado `download_model.py` na raiz do projeto.
2. Cole o código abaixo e execute-o (`python download_model.py`).

```python
from sentence_transformers import SentenceTransformer
import os

# Define o modelo e o caminho de destino
model_name = 'paraphrase-multilingual-mpnet-base-v2'
save_path = os.path.join('modelos', model_name)

print(f"Iniciando download do modelo '{model_name}'...")
model = SentenceTransformer(model_name)
model.save(save_path)
print(f"Sucesso! Modelo salvo em: {save_path}")
```

## 🛠️ Setup de Desenvolvimento

1. **Pré-requisitos**

- Python 3.10 ou superior.
- Conta no Supabase (Project URL e Anon Key).
- Dependências de Sistema:
    - Tesseract OCR e Poppler instalados e adicionados ao PATH (ou presentes nas pastas locais /tesseract e /poppler).

2. **Ambiente Virtual e Dependências**

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar pacotes
pip install -r requirements.txt
```

3. **Variáveis de Ambiente**

Crie um arquivo .env na raiz do projeto com as credenciais do seu backend:

```bash
SUPABASE_URL="sua_url_do_projeto_supabase"
SUPABASE_KEY="sua_anon_key_publica"
```

> **Segurança**: A chave da API do Google Gemini NÃO deve estar neste arquivo. Ela deve ser configurada exclusivamente nos Secrets do Supabase com a chave `GEMINI_API_KEY_EDGE`.

4. **Executar a Aplicação**

Com o modelo baixado e as dependências instaladas:

```bash
python docusmart_app.py
```

## 📦 Build e Distribuição

Para gerar o executável autônomo (`.exe`) para distribuição em Windows. O arquivo `.spec` já está configurado para incluir os binários do Tesseract, Poppler e o ícone.

**Nota**: Certifique-se de que a pasta `modelos/` foi gerada antes de rodar este comando.

```bash
# O executável será gerado na pasta dist/
pyinstaller DocuSmartApp.spec
```