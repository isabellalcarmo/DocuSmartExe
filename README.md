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