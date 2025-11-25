# DocuSmart

![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)
![Licença](https://img.shields.io/badge/licença-MIT-blue)

---

## 📖 Sobre o Projeto

O **DocuSmart** é uma aplicação de desktop projetada para a **organização e classificação automática de arquivos digitais** com base em seu conteúdo. O projeto visa solucionar a desordem digital enfrentada por profissionais e usuários domésticos, automatizando o processo de triagem e arquivamento de documentos.

### Principais Funcionalidades

* **Classificação com IA**: Utiliza tanto um modelo de IA local para garantir privacidade e rapidez quanto a API do Google Gemini para análises de maior complexidade e acurácia.
* **Suporte a Múltiplos Formatos**: Realiza a extração de conteúdo de arquivos PDF, documentos do Office e imagens.
* **Gestão de Categorias**: Permite ao usuário criar, editar e gerenciar suas próprias categorias de organização, adaptando o software ao seu fluxo de trabalho.
* **Fluxo de Revisão Interativo**: Antes de qualquer arquivo ser movido, o sistema apresenta uma pré-visualização completa, permitindo que o usuário valide ou corrija as sugestões da IA, garantindo total controle sobre o resultado final.

Desenvolvido como uma ferramenta utilitária funcional, o DocuSmart serve como uma prova de conceito para um sistema de organização documental assistido por IA. Foi concebido para atender a **profissionais, pesquisadores e usuários domésticos** que necessitam gerenciar e organizar seus documentos digitais locais de forma eficiente.

### ⚠️ Ressalvas Importantes

* A aplicação depende de uma infraestrutura de backend externa (**Supabase**) para autenticação e execução de funções de nuvem.
* A funcionalidade completa requer a instalação de software de terceiros no sistema do usuário (**Tesseract** e **Poppler**).
* A classificação avançada (via Gemini) exige a configuração de chaves de API para serviços externos, o que pode incorrer em custos.

## 👁️ Visão de Projeto

Esta seção contém cenários que orientam o projeto, uso e evolução do DocuSmart. Os cenários positivos expressam a intenção da ferramenta, enquanto os negativos expõem limitações conhecidas e esperadas, ajudando a balizar as expectativas de uso.

### Cenários Positivos (Uso Esperado)

#### Cenário Positivo 1: Usuário Profissional, IA na Nuvem e Revisão Manual

Ana, advogada, precisa organizar a pasta de um novo caso que recebeu por e-mail, contendo dezenas de arquivos misturados: PDFs de petições, planilhas de custos e fotos de documentos. Ela salva tudo em uma pasta, abre o DocuSmart, seleciona o diretório e, como sabe que os arquivos precisam ser organizados com alta precisão, escolhe a opção "Visualizar (IA Gemini)". A aplicação analisa cada arquivo e realiza a extração dos seus conteúdos. Na tela de pré-visualização, Ana vê que a IA classificou corretamente as petições em "Jurídico", as planilhas em "Financeiro" e as fotos dos documentos em "Imagens". Ela nota, porém, que um documento de identidade foi classificado como "Outros". Ana simplesmente clica em "Modificar" ao lado do arquivo, altera a categoria para "Jurídico" e, com um clique, confirma a organização. Em segundos, sua pasta está limpa e estruturada.

#### Cenário Positivo 2: Usuário Doméstico, Modelo Local e Descoberta

Bruno está digitalizando documentos antigos da família e tem uma pasta com centenas de arquivos, incluindo fotos, certidões de nascimento (`.pdf`) e cartas antigas (`.txt`). Ele não quer usar créditos de IA e prefere manter a análise local por privacidade. Ele abre o DocuSmart, seleciona sua pasta e clica em "Visualizar (Modelo Local)". O programa inicia a análise usando o modelo SBERT embarcado. Na prévia, ele vê que o sistema criou automaticamente as pastas "Pessoal" (para as certidões), "Imagens" (para as fotos) e "Outros". Na tela de pré-visualização, Bruno vê que as cartas em `.txt` foram para "Outros" porque o conteúdo era muito curto e vago. Ele decide que está bom por enquanto, confirma a organização e fica satisfeito por ter separado automaticamente os documentos das fotos sem esforço.

### Cenários Negativos (Limitações Conhecidas)

#### Cenário Negativo 1: Limitação de Ambiente (Dependências Locais e OCR)

Carlos, um usuário com pouco conhecimento técnico, baixa o DocuSmart para organizar seus comprovantes de Imposto de Renda. Sua pasta contém PDFs escaneados (imagens sem texto selecionável) e fotos de recibos (`.png`) tiradas com o celular. Ele se autentica e, para economizar créditos, escolhe a opção "Visualizar (Modelo Local)". Para sua frustração, a pré-visualização classifica a maioria dos seus arquivos na categoria "Outros (Não processável)". Isso ocorre porque a funcionalidade de OCR (Reconhecimento Óptico de Caracteres) do programa depende de ferramentas externas (Tesseract e Poppler) que não vêm pré-instaladas com o software e exigem configuração manual no sistema operacional. Sem essas dependências, o modelo local é "cego" para o conteúdo de imagens. Além disso, Carlos nota que, mesmo após instalar as ferramentas, alguns recibos amassados ou com baixa iluminação continuam não sendo reconhecidos, evidenciando que o modelo local tem menor precisão e robustez se comparado à IA na nuvem.

#### Cenário Negativo 2: Limitação da IA (Sobrecarga de Recurso e Ambiguidade)

Diana, uma arquiteta, utiliza a opção "Visualizar (IA Gemini)" para organizar os documentos de uma reforma antiga. A pasta contém dois tipos de arquivos problemáticos: (1) digitalizações de plantas e escrituras em altíssima resolução (arquivos PDF pesados, acima de 10MB) e (2) arquivos de texto com anotações muito breves e vagas (ex: um `notas.txt` contendo apenas a frase "verificar medidas"). Ao processar, Diana percebe que o sistema demora e, para os arquivos pesados, a aplicação classificou o arquivo como "Outros (Não processável)" ou os joga para "Outros". Isso acontece porque o envio de arquivos muito grandes converte o documento para um formato de texto (Base64) que excede o limite de memória RAM das funções do servidor (Edge Functions), causando um erro de infraestrutura (`503 Service Unavailable`). Já o arquivo `notas.txt` também vai para "Outros", não por erro técnico, mas porque a IA não possui contexto semântico suficiente para decidir se aquilo é "Financeiro", "Jurídico" ou "Pessoal". Este cenário ilustra que a IA não é infalível: ela possui limites físicos (tamanho do arquivo/memória do servidor) e limites lógicos (necessidade de contexto mínimo no conteúdo).

## 🛠️ Documentação Técnica do Projeto

Esta seção destina-se a desenvolvedores e colaboradores que desejam entender a estrutura interna, reutilizar componentes ou evoluir o **DocuSmart**. O software opera sob uma arquitetura modular híbrida (Desktop + Nuvem), centralizando configurações sensíveis e garantindo compatibilidade entre diferentes sistemas operacionais.

### 1. Especificação de Requisitos

Abaixo estão listados os requisitos que guiaram o desenvolvimento do software, divididos entre o que o sistema *faz* (Funcionais) e *como* ele deve operar (Não-Funcionais).

#### Requisitos Funcionais (RF)
* **RF01 - Distribuição Controlada e Autenticação:**
    * O acesso ao software é restrito. O usuário interessado deve realizar um cadastro prévio (via formulário web ou contato direto).
    * Após a validação cadastral e aprovação pelo administrador no banco de dados (tabela `profiles`, campo `is_approved` = true), o usuário receberá o executável (`DocuSmartApp.exe`) oficialmente por e-mail.
    * Ao abrir o executável, o usuário deve realizar o login com as credenciais cadastradas. O sistema validará se a conta existe e se o status de aprovação está ativo antes de liberar o acesso às funcionalidades.
* **RF02 - Inicialização e Conectividade:** O sistema deve verificar a conexão com a internet (pingando `google.com`) antes de iniciar a interface gráfica e carregar variáveis de ambiente seguras (`.env`) para conectar ao backend.
* **RF03 - Autenticação e Sessão:** O sistema deve permitir login e cadastro de usuário utilizando o cliente Supabase inicializado globalmente, mantendo o estado da sessão (usuário atual e token) acessível para todos os módulos.
* **RF04 - Seleção e Gestão de Diretórios:** O usuário deve poder selecionar uma pasta local para organização, sendo o sistema capaz de listar e filtrar arquivos suportados.
* **RF05 - Classificação Híbrida (Estratégia de Fallback):**
    * **Nível 1 (Nuvem):** Uso de Edge Functions e IA Generativa (Google Gemini) para classificação semântica de alta precisão, consumindo créditos do usuário.
    * **Nível 2 (Local):** Uso de modelo SBERT (`paraphrase-multilingual-mpnet-base-v2`) e Regex para classificação offline e gratuita quando não houver créditos ou internet.
* **RF06 - Extração de Texto (OCR/Parsing):** Extração de texto de múltiplos formatos (`.pdf`, `.docx`, imagens, planilhas) com integração de OCR (Tesseract/Poppler) para documentos digitalizados.
* **RF07 - Visualização e Auditoria:** Apresentar uma prévia da estrutura de pastas proposta, permitindo ao usuário modificar manualmente a categoria de qualquer arquivo antes da execução.
* **RF08 - Cache de Processamento:** Armazenar o hash SHA-256 dos arquivos já processados para evitar consumo duplicado de recursos (tempo/créditos).

#### Requisitos Não-Funcionais (RNF)
* **RNF01 - Compatibilidade com Windows:** O sistema deve implementar políticas de *Event Loop* específicas (`WindowsSelectorEventLoopPolicy`) para evitar erros de concorrência da biblioteca `asyncio` em ambientes Windows.
* **RNF02 - Segurança de Configuração:** As credenciais de API (`SUPABASE_URL`, `SUPABASE_KEY`) não devem estar "chumbadas" no código fonte, mas carregadas dinamicamente via variáveis de ambiente usando `python-dotenv`.
* **RNF03 - Gerenciamento de Estado Global (Singleton):** A instância do cliente de banco de dados (`supabase`) deve ser um Singleton acessível globalmente para evitar múltiplas conexões e garantir consistência de dados.
* **RNF04 - Interface Gráfica Responsiva:** A interface deve ser construída em `CustomTkinter` e executar tarefas pesadas em *threads* separadas para não congelar a janela principal.

### 2. Descrição da Arquitetura e Dados

O DocuSmart utiliza uma arquitetura modular onde a configuração e o estado são desacoplados da interface e da lógica de negócio.

#### Módulos Principais
1.  **Módulo de Configuração (`config.py`):**
    * Atua como o ponto central de verdade ("Single Source of Truth") para o estado da aplicação.
    * Responsável por carregar o arquivo `.env` usando `dotenv`.
    * Inicializa e armazena a instância global do cliente `supabase`.
    * Mantém variáveis globais de sessão como `current_user` e `gemini_api_key` e fornece utilitários de infraestrutura (`check_internet_connection`).
2.  **Patch de Compatibilidade (`fix_asyncio.py`):**
    * Módulo isolado responsável por corrigir o comportamento do loop de eventos do Python no Windows, prevenindo erros de *Runtime* (como `Event loop is closed`) ao usar bibliotecas assíncronas de terceiros.
3.  **Cliente Desktop (`docusmart_app.py`):** Camada de Interface (View/Controller) que gerencia a interação com o usuário.
4.  **Motor de Processamento (`organizer.py`):** Camada de Lógica (Model) que executa a manipulação de arquivos, extração de texto e chamadas de API.

#### Fluxo de Inicialização
1.  O sistema carrega `fix_asyncio.py` para ajustar o ambiente de execução.
2.  O módulo `config.py` é importado, carregando as variáveis de ambiente e testando a conectividade via `requests.head`.
3.  A função `init_supabase()` tenta criar a conexão com o backend. Falhas aqui são tratadas silenciosamente para permitir depuração, mas logadas no console.
4.  A interface gráfica `docusmart_app.py` é iniciada, consumindo o objeto `supabase` já instanciado.

#### Modelo de Dados Local
* **Cache (`cache_{user_id}.json`):** Armazenamento chave-valor local (JSON) onde a chave é o Hash SHA-256 do arquivo e o valor é a categoria atribuída. Isso permite persistência de decisões entre sessões.

### 3. Configuração do Backend e Infraestrutura (Supabase)

O backend do DocuSmart foi construído sobre a plataforma **Supabase**, utilizando uma arquitetura *serverless* para garantir escalabilidade e segurança. Abaixo estão detalhadas as configurações realizadas nos principais módulos do serviço.

#### Banco de Dados e Tabelas (PostgreSQL)
O banco de dados foi estruturado para gerenciar os dados complementares dos usuários que não são nativos do módulo de autenticação.

* **Tabela `profiles`:** Criada para estender as informações do usuário. Esta tabela possui uma relação *um-para-um* com a tabela interna `auth.users`.
    * **Colunas Principais:** `id` (chave estrangeira ligada ao auth.uid), `full_name`, `credits_remaining` (saldo para uso da IA) e `is_approved` (booleano para controle de acesso).
* **Triggers e Functions (PL/pgSQL):** Foi configurada uma *Trigger* automática no banco de dados (`on_auth_user_created`) para que, sempre que um novo usuário se cadastre no sistema, uma entrada correspondente seja criada automaticamente na tabela `profiles` com os valores padrão (créditos zerados e aprovação pendente).

#### Autenticação (Auth)
O módulo de autenticação foi configurado para suportar o fluxo de entrada via E-mail e Senha.

* **Provedor:** Habilitado o provedor "Email" nativo.
* **Confirmação de E-mail:** A opção "Enable Email Confirmations" foi mantida ativa para garantir a veracidade dos cadastros. O usuário só consegue efetuar login após clicar no link enviado.
* **Templates de E-mail:** Os modelos de e-mail ("Confirm Your Signup" e "Reset Password") foram personalizados para refletir a identidade visual do DocuSmart e redirecionar o usuário para as páginas de feedback corretas (ex: Landing Page do Lovable).

#### Edge Functions (Lógica Serverless)
Para integrar a Inteligência Artificial sem expor chaves de API no cliente Desktop, foram desenvolvidas e implantadas duas **Supabase Edge Functions** utilizando Deno e TypeScript.

* **Função `classify-document-file`:**
    * **Objetivo:** Receber arquivos binários (PDFs/Imagens) codificados em Base64 e enviá-los para a API do Google Gemini.
    * **Configuração:** Ajustada para utilizar o modelo `gemini-2.0-flash` na versão `v1` da API, garantindo maior estabilidade e suporte a arquivos.
    * **Segurança:** Validação de token JWT ativa para garantir que apenas usuários logados possam invocá-la.
* **Função `classify-document-gemini`:**
    * **Objetivo:** Receber texto puro extraído localmente e classificá-lo semanticamente.
    * **Configuração:** Possui lógica de *fallback* robusta para interpretar respostas da IA e convertê-las em categorias JSON válidas.
* **Deploy:** As funções foram implantadas via Supabase CLI (`supabase functions deploy`), garantindo versionamento e atualização rápida sem necessidade de redistribuir o executável do cliente.

#### Gerenciamento de Segredos (Secrets)
A segurança das chaves de API foi priorizada através do uso de variáveis de ambiente em dois níveis:

* **No Cliente (Desktop):** As credenciais de conexão com o Supabase (`SUPABASE_URL` e `SUPABASE_KEY`) são injetadas via arquivo `.env` e carregadas pela biblioteca `python-dotenv` durante a inicialização, evitando que fiquem expostas diretamente no código fonte.
* **No Servidor (Edge Functions):** A chave da API do Google Gemini (`GEMINI_API_KEY_EDGE`) não trafega pela rede. Ela foi configurada diretamente no cofre de segredos do Supabase via CLI (`supabase secrets set`), sendo acessível apenas pelo ambiente de execução do servidor (Deno).

#### Políticas de Segurança (RLS)
Foi ativado o **Row Level Security (RLS)** na tabela `profiles`.
* **Política de Leitura:** Usuários só podem ler ("SELECT") os dados da sua própria linha (onde `auth.uid() == id`).
* **Política de Atualização:** O campo de créditos (`credits_remaining`) é gerenciado pelo sistema, garantindo que usuários não possam alterar seu próprio saldo arbitrariamente.

### 4. Descrição Funcional (O Pipeline de Organização)

O pipeline de organização implementado em `organizer.py` segue o fluxo lógico abaixo:

1.  **Identificação e Hash:** O arquivo é lido e seu hash único é calculado.
2.  **Verificação de Cache:** Se o hash existe no JSON local, a categoria é recuperada imediatamente.
3.  **Verificação de Créditos:** O sistema consulta o objeto `config.current_user` para validar se há saldo para uso da IA.
4.  **Decisão de Roteamento (Strategy Pattern):**
    * *Com Créditos + Internet:* Tenta classificação via Edge Function (Google Gemini). Se falhar (erro 503/timeout), faz fallback automático.
    * *Sem Créditos/Internet:* Usa modelo local SBERT.
5.  **Execução:** Move os arquivos fisicamente para a estrutura de pastas aprovada, resolvendo conflitos de nomes.

### 5. Sobre o Código

Esta seção detalha as técnicas de programação, bibliotecas e padrões de projeto utilizados.

* **Linguagem:** Python 3.10+ (Cliente) e TypeScript/Deno (Edge Functions).
* **Bibliotecas e Dependências Chave:**
    * `python-dotenv`: Utilizado para separar configurações sensíveis do código fonte, facilitando a segurança em repositórios públicos.
    * `requests`: Utilizado para verificações de conectividade síncronas (`check_internet_connection`) com timeout definido.
    * `supabase`: SDK oficial para comunicação com o BaaS.
    * `customtkinter`: Framework de UI moderno.
* **Estratégia de Asyncio (Windows):**
    * O código utiliza `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` explicitamente. Isso é necessário porque o padrão `ProactorEventLoop` no Windows (padrão no Python 3.8+) causa falhas ao fechar conexões SSL/Sockets em subprocessos, o que afetaria a biblioteca do Supabase.
* **Padrão Singleton (Config):**
    * O arquivo `config.py` implementa um padrão Singleton implícito. A variável `supabase` é inicializada como `None` e instanciada apenas uma vez na função `init_supabase`, sendo depois importada por outros módulos sem re-instanciação, garantindo uma única conexão ativa.
* **Tratamento de Exceções:**
    * O módulo de configuração captura exceções genéricas na inicialização do Supabase e na verificação de internet (`requests.ConnectionError`, `requests.Timeout`) para garantir que a aplicação não encerre abruptamente durante o *boot*, permitindo tratamento de erro gracioso na UI.

### 6. Compilação e Geração do Executável (Build)

Para distribuir a aplicação aos usuários finais, o código fonte Python deve ser "congelado" em um executável autônomo (`.exe`) que contenha todas as dependências (bibliotecas, interpretador Python, arquivos de modelo e ícones).

**Pré-requisitos de Build:**
* Ambiente Python configurado com todas as dependências do `requirements.txt` instaladas.
* Biblioteca `PyInstaller` instalada.
* Arquivo de especificação `DocuSmartApp.spec` configurado corretamente na raiz do projeto.
* Arquivo de ícone `robot-head.ico` presente na raiz.

**Comando de Geração:**
Para gerar uma nova versão do executável, execute o seguinte comando no terminal, na raiz do projeto:

```bash
pyinstaller DocuSmartApp.spec
```

## 📖 Manual de Utilização para Usuários Contemplados

Este manual foi elaborado para guiar todos os tipos de usuários no uso seguro e eficiente do **DocuSmart**. Siga os roteiros abaixo para realizar as principais tarefas do sistema.

### 1. Instalação, Cadastro e Acesso ao Sistema

Diferente de programas convencionais, o DocuSmart é uma ferramenta exclusiva distribuída sob aprovação. Esta seção guia você desde o recebimento do arquivo até o seu primeiro login.

> **📋 Guia de Obtenção e Instalação**
>
> **Para INSTALAR O PROGRAMA NO SEU COMPUTADOR faça:**
>
> 1.  **Solicitação:** Realize seu cadastro inicial ou solicitação de acesso em [https://preview--smartdoc-organizer-ai.lovable.app/](https://preview--smartdoc-organizer-ai.lovable.app/).
> 2.  **Recebimento:** Após a aprovação, você receberá um e-mail oficial contendo o arquivo `DocuSmartApp.exe` (ou um link seguro para baixá-lo).
> 3.  **Instalação:** Salve o arquivo em uma pasta segura no seu computador (ex: "Documentos/DocuSmart").
>     * *Nota:* Como é um executável portátil, não é necessário rodar um instalador. Basta salvar o arquivo na pasta desejada.
> 4.  **Atalho (Opcional):** Clique com o botão direito no arquivo, selecione "Enviar para" > "Área de Trabalho (criar atalho)" para facilitar o acesso futuro.

> **📋 Guia de Acesso (Login e Cadastro)**
>
> **Para ENTRAR NA SUA CONTA OU CADASTRAR-SE faça:**
>
> 1.  Dê um clique duplo no ícone do robô ou no atalho criado para abrir o DocuSmart. A janela **"Acesso DocuSmart"** será exibida.
> 2.  **Se você já possui conta ativa:**
>     * Digite seu *E-mail* e *Senha* nos campos indicados.
>     * Clique no botão **"Entrar"**.
> 3.  **Se for seu primeiro acesso (e ainda não tiver senha):**
>     * Clique no botão **"Criar Conta"**.
>     * Preencha seu *Nome Completo*, *Email* e escolha uma *Senha* (mínimo de 6 caracteres).
>     * Clique em **"Cadastrar"**.
> 4.  **Ativação:** Após o cadastro, acesse sua caixa de entrada de e-mail, abra a mensagem de confirmação enviada pelo sistema e clique no link de ativação. Só então retorne ao aplicativo para fazer o login.
>
> *>>> Dica: Se esqueceu sua senha, clique no link "Esqueceu sua senha?" na tela de login para abrir a página de redefinição no seu navegador padrão.*

**⚠️ Exceções ou Potenciais Problemas**

* **Se o sistema exibir:** `Erro: Sem conexão com a internet`
    * **Então faça:** Verifique se o seu cabo de rede ou Wi-Fi estão conectados. O DocuSmart precisa de internet para validar suas credenciais de segurança.

* **Se o sistema exibir:** `Sua conta ainda está aguardando aprovação`
    * **É porque:** Seu cadastro foi realizado com sucesso, mas o administrador do sistema ainda não liberou seu acesso manualmente no painel administrativo. O login será bloqueado até que essa aprovação ocorra.

* **Se o sistema exibir:** `E-mail ou senha inválidos`
    * **Então faça:** Verifique se digitou o e-mail corretamente (ex: sem espaços extras) e se a tecla *Caps Lock* não está ativada acidentalmente.

---

### 2. Gerenciamento de Categorias (Configuração)

Esta função permite personalizar como o DocuSmart deve classificar seus arquivos.

> **📋 Guia de Instruções**
>
> **Para CRIAR, EDITAR OU REMOVER CATEGORIAS faça:**
>
> 1.  Na tela principal, clique no botão **"⚙️ Gerenciar Categorias"** .
> 2.  **Para Adicionar:**
>     * Vá até a seção "Adicionar Nova Categoria".
>     * Digite o *Nome* (ex: "Escola" ou "Notas Fiscais").
>     * Digite uma *Descrição* detalhada sobre o que deve ser guardado nela.
>     * Clique em **"➕ Adicionar Categoria"**.
> 3.  **Para Remover:** Localize a categoria desejada na lista superior e clique no botão **"Remover"** ao lado dela.
> 4.  **Para Salvar:** Clique em **"✅ Salvar e Fechar"** para aplicar suas alterações.
>
> *>>> Alternativa Inteligente: Se estiver sem criatividade para a descrição, digite apenas o Nome da categoria e clique no botão "Sugerir Descrição com IA ✨". O sistema escreverá a descrição para você automaticamente.*

**⚠️ Exceções ou Potenciais Problemas**

* **Se você tentar remover as categorias:** `Outros` ou `Imagens`
    * **É porque:** Estas são categorias essenciais do sistema e são protegidas. "Outros" recebe arquivos desconhecidos e "Imagens" recebe fotos sem texto legível, garantindo que nenhum arquivo se perca.

* **Se o sistema avisar:** `A categoria já existe`
    * **Então faça:** Escolha um nome diferente para sua nova categoria ou, se quiser mudar a descrição da existente, remova a antiga primeiro e adicione-a novamente com o novo texto.

---

### 3. Organização de Documentos (Execução)

Esta é a tarefa principal do sistema: ler uma pasta bagunçada e sugerir uma organização.

> **📋 Guia de Instruções**
>
> **Para ORGANIZAR UMA PASTA DE ARQUIVOS faça:**
>
> 1.  Clique no botão **"📂 Selecionar Pasta"** e navegue até o diretório no seu computador onde estão os arquivos que deseja organizar.
> 2.  Confirme se o caminho da pasta selecionada aparece na tela.
> 3.  Escolha o **Modo de Organização**:
>     * **Opção A (Modelo Local):** Clique em **"🔍 Visualizar (Modelo Local)"**. Use esta opção para arquivos simples, gratuitos e sem necessidade de internet.
>     * **Opção B (Inteligência Artificial):** Clique em **"✨ Visualizar (IA Gemini)"**. Use esta opção para documentos complexos ou ambíguos. Note que isso consumirá seus créditos.
> 4.  Aguarde enquanto a barra de progresso processa seus arquivos 
>
> *>>> Contexto: Se você escolher a IA Gemini mas tiver, por exemplo, 50 arquivos e apenas 10 créditos, o sistema processará os 10 primeiros com a IA e o restante com o Modelo Local automaticamente.*

**⚠️ Exceções ou Potenciais Problemas**

* **Se o botão estiver desativado:** `Visualizar (IA Gemini)`
    * **É porque:** Seu saldo de créditos acabou. Você deve utilizar o "Modelo Local" ou solicitar uma recarga ao administrador.

* **Se a barra de progresso parecer travada:**
    * **É porque:** A pasta pode conter arquivos muito grandes (vídeos ou PDFs de alta resolução). O sistema pode demorar alguns minutos para extrair o texto ou enviar os dados para a nuvem. Aguarde a conclusão sem fechar o programa.

---

### 4. Revisão e Confirmação (Prévia)

Esta etapa permite que você tenha controle total sobre o resultado antes que qualquer arquivo seja movido de lugar.

> **📋 Guia de Instruções**
>
> **Para REVISAR O RESULTADO E MOVER OS ARQUIVOS faça:**
>
> 1.  Após o processamento, a janela **"Prévia da Organização"** será aberta automaticamente 
> 2.  Role a lista para ver a estrutura de pastas sugerida (ex: `📂 Financeiro/`).
> 3.  **Para Corrigir um Erro:** Se um arquivo foi classificado errado, clique no botão **"Modificar"** ao lado do nome dele e selecione a categoria correta na lista.
> 4.  **Para Finalizar:** Se estiver satisfeito com a organização, clique em **"✅ Confirmar Organização"**.
> 5.  O sistema moverá os arquivos fisicamente no seu computador e exibirá uma mensagem de sucesso.

**⚠️ Exceções ou Potenciais Problemas**

* **Se um arquivo aparecer em:** `🚫 Outros (Não processável)`
    * **É porque:** O arquivo está corrompido, protegido por senha ou é uma imagem onde o texto não pôde ser lido pelo OCR. Ele será movido para uma pasta "Outros (Não processável)" para que você o verifique manualmente depois.

* **Se o sistema avisar:** `Arquivo já existe. Renomeando...`
    * **É porque:** A pasta de destino já contém um arquivo com o mesmo nome. Para evitar sobrescrever e perder seus dados, o DocuSmart salvará o novo arquivo adicionando um número ao final (ex: `contrato_1.pdf`).