import subprocess
import sys
import os


# Patch para PyInstaller em Windows não abrir janela de console para subprocessos
if sys.platform == "win32" and getattr(sys, 'frozen', False):
    _original_Popen = subprocess.Popen

    def _patched_popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = 0
        kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
        return _original_Popen(*args, **kwargs)
    subprocess.Popen = _patched_popen


import shutil
import re
import dateparser
import config
import docx
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util
import cv2
import numpy as np
from pdf2image import convert_from_path
import fitz
import openpyxl
from pptx import Presentation
from bs4 import BeautifulSoup
import config
import json
from postgrest.exceptions import APIError


def get_tesseract_path():
    if getattr(sys, 'frozen', False): 
        base_path = sys._MEIPASS
    else: 
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'tesseract', 'tesseract.exe')


def configure_tesseract():
    tess_path = get_tesseract_path()
    tessdata_path = os.path.join(os.path.dirname(tess_path), 'tessdata')
    pytesseract.pytesseract.tesseract_cmd = tess_path
    os.environ['TESSDATA_PREFIX'] = tessdata_path
    print(f"Tesseract Path: {tess_path}")
    print(f"Tessdata Prefix: {tessdata_path}")


def get_poppler_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'poppler-24.08.0', 'Library', 'bin')


def preprocess_image(pil_image):
    try:
        img = np.array(pil_image.convert('RGB')) 
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return Image.fromarray(thresh)
    except Exception as e:
        print(f"Erro no pré-processamento da imagem: {e}")
        return pil_image 


def extract_from_pdf(file_path):
    text = ""
    max_pages_to_try_extraction = 50 
    min_text_length_for_ocr_fallback = 100 

    try:
        doc = fitz.open(file_path)
        num_pages_to_process = min(doc.page_count, max_pages_to_try_extraction)
        for i in range(num_pages_to_process):
            page = doc.load_page(i)
            text += page.get_text("text") 
        doc.close()

        if len(text.strip()) < min_text_length_for_ocr_fallback and doc.page_count > 0 : 
            print(f"Texto curto extraído de '{os.path.basename(file_path)}', tentando OCR como fallback.")
            ocr_text_accumulator = ""
            max_pages_for_ocr = min(doc.page_count, 5) 
            images = convert_from_path(file_path, poppler_path=get_poppler_path(), dpi=300, first_page=1, last_page=max_pages_for_ocr)
            for i, image in enumerate(images):
                preprocessed_image = preprocess_image(image)
                page_ocr_text = pytesseract.image_to_string(preprocessed_image, lang='por+eng')
                if page_ocr_text:
                    ocr_text_accumulator += f"\n--- OCR Page {i+1} ---\n" + page_ocr_text.strip() + "\n"
            
            if len(ocr_text_accumulator.strip()) > len(text.strip()):
                text = ocr_text_accumulator
            else: 
                text += ocr_text_accumulator 
    except Exception as e:
        print(f"Erro ao extrair texto do PDF '{os.path.basename(file_path)}': {e}")
        return "" 
    return text.strip()


def extract_from_docx(file_path):
    text_content = []
    max_paragraphs = 500 
    try:
        doc = docx.Document(file_path)
        paragraphs_processed = 0
        for paragraph in doc.paragraphs:
            if paragraphs_processed >= max_paragraphs:
                break
            text_content.append(paragraph.text)
            paragraphs_processed += 1
        return "\n".join(text_content).strip()
    except Exception as e:
        print(f"Erro ao extrair texto do DOCX '{os.path.basename(file_path)}': {e}")
        return ""


def extract_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: 
            return f.read().strip()
    except Exception as e:
        print(f"Erro ao extrair texto do TXT '{os.path.basename(file_path)}': {e}")
        return ""


def extract_from_image(file_path):
    try:
        image = Image.open(file_path)
        preprocessed_image = preprocess_image(image) 
        text = pytesseract.image_to_string(preprocessed_image, lang='por+eng')
        return text.strip()
    except Exception as e:
        print(f"Erro ao extrair texto da Imagem '{os.path.basename(file_path)}': {e}")
        return ""


def extract_from_xlsx(file_path):
    text_content = []
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            for row in sheet.iter_rows():
                row_text = [str(cell.value) for cell in row if cell.value is not None]
                if row_text:
                    text_content.append(" | ".join(row_text))
        return "\n".join(text_content).strip()
    except Exception as e:
        print(f"Erro ao extrair texto do XLSX '{os.path.basename(file_path)}': {e}")
        return ""


def extract_from_pptx(file_path):
    text_content = []
    max_slides_to_process = 20 
    try:
        prs = Presentation(file_path)
        slides_processed = 0
        for slide in prs.slides:
            if slides_processed >= max_slides_to_process:
                break
            for shape in slide.shapes:
                if hasattr(shape, "text_frame") and shape.text_frame: 
                    for paragraph in shape.text_frame.paragraphs: 
                        for run in paragraph.runs: 
                            text_content.append(run.text)
                elif hasattr(shape, "text"): 
                    text_content.append(shape.text)
            slides_processed += 1
        return "\n".join(text_content).strip()
    except Exception as e:
        print(f"Erro ao extrair texto do PPTX '{os.path.basename(file_path)}': {e}")
        return ""


def extract_from_html(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "aside"]): 
            element.extract()
        text = soup.get_text(separator='\n', strip=True) 
        return text.strip()
    except Exception as e:
        print(f"Erro ao extrair texto do HTML '{os.path.basename(file_path)}': {e}")
        return ""


def extract_text_from_file(file_path):
    extension = os.path.splitext(file_path)[1].lower() 
    print(f"Arquivo: {os.path.basename(file_path)}, extensão: {extension}")
    try:
        if extension == '.pdf':
            return extract_from_pdf(file_path)
        elif extension == '.docx':
            return extract_from_docx(file_path)
        elif extension == '.txt':
            return extract_from_txt(file_path)
        elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
            return extract_from_image(file_path)
        elif extension == '.xlsx':
            return extract_from_xlsx(file_path)
        elif extension == '.pptx':
            return extract_from_pptx(file_path)
        elif extension in ['.html', '.htm']:
            return extract_from_html(file_path)
        else:
            return "Formato de arquivo não suportado."
    except Exception as e:
        print(f"Erro geral ao tentar extrair texto de '{os.path.basename(file_path)}': {e}")
        return f"Erro ao processar arquivo: {e}"


def extract_dates(text_content):
    if not text_content: return []
    pattern = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b' 
    found_dates_str = re.findall(pattern, text_content)
    parsed_dates = []
    for date_str_val in found_dates_str:
        try:
            dt = dateparser.parse(date_str_val, languages=['pt', 'en']) 
            if dt:
                parsed_dates.append(dt)
        except Exception as e:
            print(f"Erro ao parsear data '{date_str_val}': {e}") 
    return parsed_dates


MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
MODEL_SUBFOLDER = os.path.join('modelos', MODEL_NAME) 


configure_tesseract() 


if getattr(sys, 'frozen', False): 
    model_path_sbert = os.path.join(sys._MEIPASS, MODEL_SUBFOLDER)
else: 
    model_path_sbert = MODEL_SUBFOLDER


try:
    print(f"Tentando carregar modelo SBERT de: {model_path_sbert}")
    model_sbert = SentenceTransformer(model_path_sbert)
    print("Modelo SBERT carregado com sucesso.")
except Exception as e:
    print(f"Erro FATAL ao carregar o modelo de linguagem SBERT: {e}")
    print(f"Verifique se o diretório '{model_path_sbert}' existe e contém o modelo.")
    print("Se for um executável, certifique-se que o PyInstaller incluiu a pasta com --add-data.")
    sys.exit("Falha ao carregar modelo SBERT. O aplicativo não pode continuar.")


def classify_content_gemini(text_content, categories_dict, gemini_api_key_in_use):
    if not gemini_api_key_in_use:
        print("Erro: Chave da API Gemini não configurada para classify_content_gemini.")
        return "Outros", 0.0 
        
    if not configure_gemini(gemini_api_key_in_use): 
        print("Erro ao (re)configurar Gemini API em classify_content_gemini.")
        return "Outros", 0.0

    if not text_content or len(text_content.strip()) < 10: 
        print("Texto muito curto para Gemini, retornando 'Outros'.")
        return "Outros", 0.0

    try:
        model_genai = genai.GenerativeModel('gemini-1.5-flash-latest') 
    except Exception as e:
        print(f"Erro ao instanciar modelo Gemini: {e}")
        return "Outros", 0.0

    category_names_list = [cat for cat in categories_dict.keys() if cat != "Outros (Não processável)"] # Lista de nomes de categorias válidas
    category_names_str = ", ".join(f"'{cat}'" for cat in category_names_list) # String formatada para o prompt
    category_descriptions_prompt = "\n".join([f"- {name}: {desc}" for name, desc in categories_dict.items() if name in category_names_list])

    prompt = f"""
    Analise o seguinte texto de um documento e classifique-o em UMA das seguintes categorias.
    Responda APENAS com o NOME EXATO da categoria da lista. Não adicione nenhuma outra palavra, explicação ou pontuação.

    Categorias Disponíveis (escolha uma da lista abaixo):
    {category_names_str} 

    Descrições para ajudar na escolha (não responda com a descrição, apenas com o nome da categoria):
    {category_descriptions_prompt}

    Texto do Documento para classificar:
    ---
    {text_content[:15000]} 
    ---

    Nome Exato da Categoria Escolhida:
    """

    try:
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=30,
            temperature=0.1 
        )
        response = model_genai.generate_content(prompt, generation_config=generation_config)

        chosen_category_raw = response.text.strip().replace("'", "").replace('"', '') # Remove aspas
        print(f"Gemini escolheu (raw): '{chosen_category_raw}'")

        if chosen_category_raw in category_names_list:
            print(f"Match exato Gemini: '{chosen_category_raw}'")
            return chosen_category_raw, 0.95 
        
        for cat_name in category_names_list:
            if cat_name.lower() == chosen_category_raw.lower():
                print(f"Match flexível (case) Gemini: '{chosen_category_raw}' -> '{cat_name}'")
                return cat_name, 0.90
            if cat_name.lower() in chosen_category_raw.lower() or chosen_category_raw.lower() in cat_name.lower():
                print(f"Match flexível (substring) Gemini: '{chosen_category_raw}' -> '{cat_name}'")
                return cat_name, 0.85 

        print(f"Gemini retornou categoria não esperada ou não mapeável: '{chosen_category_raw}'. Usando 'Outros'.")
        return "Outros", 0.3 
    except Exception as e:
        print(f"Erro durante a chamada à API Gemini: {e}")
        if hasattr(e, 'message') and "rate limit" in str(e.message).lower():
            print("Rate limit do Gemini atingido.") 
        return "Outros", 0.0


def classify_content_gemini_via_edge(text_content, categories_dict):
    if not config.supabase:
        print("ERRO: Cliente Supabase não inicializado em config.py.")
        return "Outros", 0.0
    if not text_content or len(text_content.strip()) < 10:
        print("Texto muito curto para enviar para Edge Function, retornando 'Outros'.")
        return "Outros", 0.0

    function_name = "classify-document-gemini"
    payload = {"document_text": text_content, "categories": categories_dict}
    
    print(f"Invocando Edge Function '{function_name}'...")
    processed_data = None

    try:
        response_from_invoke = config.supabase.functions.invoke(function_name, invoke_options={'body': payload})

        print(f"DEBUG: Tipo da resposta da Edge Function: {type(response_from_invoke)}")
        if isinstance(response_from_invoke, bytes):
            try:
                print(f"DEBUG: Resposta da Edge Function (bytes decodificados): {response_from_invoke.decode('utf-8', errors='replace')[:500]}...")
            except Exception as decode_err:
                print(f"DEBUG: Não foi possível decodificar a resposta bytes: {decode_err}")
        else:
            print(f"DEBUG: Resposta da Edge Function (não bytes): {response_from_invoke}")

        if isinstance(response_from_invoke, dict):
            processed_data = response_from_invoke
        elif isinstance(response_from_invoke, bytes):
            decoded_response_str = response_from_invoke.decode('utf-8', errors='ignore')
            try:
                processed_data = json.loads(decoded_response_str)
            except json.JSONDecodeError:
                print(f"ERRO: Edge Function retornou bytes que não são JSON: {decoded_response_str}")
                return "Outros", 0.0 
        else:
            print(f"ERRO: Tipo de resposta inesperado da Edge Function: {type(response_from_invoke)}")
            return "Outros", 0.0

        if not processed_data:
            print("ERRO: Nenhum dado processável recebido da Edge Function.")
            return "Outros", 0.0

        if "error" in processed_data and processed_data["error"] is not None:
            print(f"Erro retornado explicitamente pela Edge Function: {processed_data['error']}")
            return "Outros", 0.0

        if "category" in processed_data:
            print(f"Resposta da Edge Function processada com sucesso: {processed_data}")
            category = processed_data.get("category", "Outros")
            confidence = processed_data.get("confidence", 0.3) 
            return category, confidence
        else:
            print(f"Resposta da Edge Function não continha 'category': {processed_data}")
            return "Outros", 0.0
    except APIError as e: 
        print(f"APIError ao invocar Edge Function '{function_name}': Status {e.status if hasattr(e, 'status') else 'N/A'} - {e.message}")
        if hasattr(e, 'json') and callable(e.json):
            try:
                error_details_json = e.json()
                print(f"Detalhes JSON da APIError: {error_details_json}")
            except Exception as json_e:
                print(f"Não foi possível parsear JSON da APIError: {json_e}")
        elif hasattr(e, 'args') and e.args:
            print(f"Detalhes da APIError (args): {e.args}")
        return "Outros", 0.0
    except Exception as e: 
        print(f"Erro Crítico Geral ao invocar Edge Function '{function_name}': {type(e).__name__} - {e}")
        return "Outros", 0.0


def classify_content_local(text, categories_embeddings_dict):
    if not text or len(text.strip()) < 5: 
        return "Outros", 0.0 

    try:
        text_embedding = model_sbert.encode(text, convert_to_tensor=True)
    except Exception as e:
        print(f"Erro ao codificar o texto localmente '{text[:50]}...': {e}")
        return "Outros", 0.0

    max_similarity = -1.0 
    best_category = "Outros"

    for category_name, description_embedding in categories_embeddings_dict.items():
        if description_embedding is None: 
            continue
        try:
            similarity = util.cos_sim(text_embedding, description_embedding).item()
        except Exception as e:
            print(f"Erro ao calcular similaridade local para categoria '{category_name}': {e}")
            continue

        if similarity > max_similarity:
            max_similarity = similarity
            best_category = category_name

    confidence_score = (max_similarity + 1) / 2
    return best_category, confidence_score


def classify_by_filename_keywords(filename, categories_dict):
    clean_filename = os.path.splitext(filename)[0].lower().replace("_", " ").replace("-", " ")

    for cat_name in categories_dict.keys():
        pattern_cat = r'\b' + re.escape(cat_name.lower()) + r'\b'
        if re.search(pattern_cat, clean_filename):
            print(f"Keyword match (palavra inteira) para '{cat_name}' em '{filename}'")
            return cat_name, 0.98 

    if re.search(r'\b(extrato|fatura|boleto|conta|holerite|imposto|recibo|nota fiscal|nf-e|nfe|danfe)\b', clean_filename):
        if "Financeiro" in categories_dict: return "Financeiro", 0.90
    elif re.search(r'\b(rg|cpf|cnh|passaporte|certidao|eleitor|nascimento|casamento|identidade|titulo eleitoral)\b', clean_filename):
        if "Pessoal" in categories_dict: return "Pessoal", 0.90
    elif re.search(r'\b(contrato|peticao|notificacao|judicial|acordo|escritura|procuracao|alvara|sentenca|termo de)\b', clean_filename):
        if "Jurídico" in categories_dict: return "Jurídico", 0.90
    elif re.search(r'\b(exame|laudo|receita|medico|vacina|consulta|historico medico|atestado|relatorio medico)\b', clean_filename):
        if "Saúde" in categories_dict: return "Saúde", 0.90
    return "Outros", 0.0


def simulate_organization(folder_path, categories_dict, progress_callback=None, use_gemini=False, available_credits_for_simulation=0):

    categories_embeddings_dict = {}
    if not use_gemini or (use_gemini and available_credits_for_simulation == 0):
        print("Modo Local ou Gemini sem créditos: Pré-calculando embeddings SBERT...")
        for category_name, description in categories_dict.items():
            if description and category_name != "Outros (Não processável)":
                try: categories_embeddings_dict[category_name] = model_sbert.encode(description, convert_to_tensor=True)
                except Exception as e: print(f"Erro ao codificar SBERT para '{category_name}': {e}"); categories_embeddings_dict[category_name] = None
            else: categories_embeddings_dict[category_name] = None
        print("Embeddings SBERT das categorias pré-calculados.")

    files_to_organize = []
    organized_structure = {}
    gemini_api_calls_count = 0 
    
    try: files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except FileNotFoundError:
        print(f"Erro: Pasta não encontrada - {folder_path}")
        if progress_callback: progress_callback(1,1) 
        return files_to_organize, organized_structure, 0 
        
    total_files = len(files_in_folder)
    if total_files == 0:
        if progress_callback: progress_callback(1, 1)
        return files_to_organize, organized_structure, 0 

    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'] 
    TITLE_KEYWORD_CONFIDENCE = 0.85    
    TITLE_SBERT_THRESHOLD = 0.65    
    CONTENT_SBERT_THRESHOLD = 0.60  

    for i, filename in enumerate(files_in_folder):
        file_path = os.path.join(folder_path, filename)
        base_filename, extension = os.path.splitext(filename)
        extension = extension.lower()

        classified_category = "Outros"
        classification_method_used = "fallback_initial" 
        date_str = "Nenhuma"

        print(f"\nProcessando: {filename}")
        text_content = extract_text_from_file(file_path)

        if text_content == "Formato de arquivo não suportado.":
            classified_category = "Outros (Não processável)"; classification_method_used = "unsupported_format"; text_content = None 
        elif extension in image_extensions and not text_content: 
            classified_category = "Imagens"; classification_method_used = "image_extension_no_ocr"; text_content = None 
        elif extension in image_extensions and text_content:
            print(f"  Imagem com OCR detectado: {filename}")
        
        if classification_method_used not in ["unsupported_format", "image_extension_no_ocr"]:
            tentar_gemini_para_este_arquivo = use_gemini and text_content and (gemini_api_calls_count < available_credits_for_simulation)
            
            if tentar_gemini_para_este_arquivo:
                print(f"  Usando IA Gemini para: {filename} (Crédito #{gemini_api_calls_count + 1} de {available_credits_for_simulation} disponíveis para esta sessão)")
                gemini_category, _ = classify_content_gemini_via_edge(text_content, categories_dict)

                if gemini_category:
                    gemini_api_calls_count += 1 

                classified_category = gemini_category 
                classification_method_used = "gemini_edge_function"
                print(f"  IA Gemini classificou como '{classified_category}'")
            else:
                if use_gemini:
                    if not text_content:
                        print(f"  IA Gemini era a intenção, mas sem texto para '{filename}'. Usando lógica local de título.")
                        classification_method_used = "local_title_no_text_for_gemini"
                    elif gemini_api_calls_count >= available_credits_for_simulation:
                        print(f"  Créditos para IA Gemini esgotados para esta simulação. Usando lógica local para: {filename}")
                        classification_method_used = "local_due_to_no_credits"
                else:
                    print(f"  Usando lógica local para: {filename}")
                    classification_method_used = "local_explicit_choice"

                kw_category, kw_confidence = classify_by_filename_keywords(filename, categories_dict)
                print(f"    Keywords no título: '{kw_category}' (Conf: {kw_confidence:.2f})")
                if kw_confidence >= TITLE_KEYWORD_CONFIDENCE and kw_category != "Outros":
                    classified_category = kw_category
                    classification_method_used = "local_keyword_title" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_keyword"
                else:
                    sbert_title_category, sbert_title_similarity = classify_content_local(base_filename, categories_embeddings_dict)
                    print(f"    SBERT no título: '{sbert_title_category}' (Conf: {sbert_title_similarity:.2f})")

                    sbert_content_category, sbert_content_similarity = ("Outros", 0.0)
                    if text_content: 
                        sbert_content_category, sbert_content_similarity = classify_content_local(text_content, categories_embeddings_dict)
                    print(f"    SBERT no conteúdo: '{sbert_content_category}' (Conf: {sbert_content_similarity:.2f})")

                    if sbert_content_similarity >= CONTENT_SBERT_THRESHOLD and sbert_content_category != "Outros":
                        if sbert_title_similarity >= TITLE_SBERT_THRESHOLD and sbert_title_category != "Outros":
                            if sbert_content_similarity > sbert_title_similarity + 0.05 : 
                                classified_category = sbert_content_category
                                classification_method_used = "local_sbert_content_preferred" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_sbert_content"
                            else:
                                classified_category = sbert_title_category
                                classification_method_used = "local_sbert_title_preferred" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_sbert_title"
                        else: 
                            classified_category = sbert_content_category
                            classification_method_used = "local_sbert_content_only" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_sbert_content"
                    elif sbert_title_similarity >= TITLE_SBERT_THRESHOLD and sbert_title_category != "Outros": 
                        classified_category = sbert_title_category
                        classification_method_used = "local_sbert_title_only" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_sbert_title"
                    else: 
                        if kw_confidence > 0 and kw_category != "Outros" and classified_category == "Outros":
                            classified_category = kw_category
                            classification_method_used = "local_keyword_title_fallback" if not classification_method_used.startswith("local_due_to_no_credits") else classification_method_used + "_then_keyword_fallback"
                        elif classified_category == "Outros":
                            current_method_prefix = "local_sbert_low_conf"
                            if classification_method_used.startswith("local_due_to_no_credits"):
                                classification_method_used += "_then_sbert_low_conf"
                            else:
                                classification_method_used = current_method_prefix

            if extension in image_extensions and text_content and classified_category == "Outros" and "Imagens" in categories_dict:
                print("  Reclassificando OCR de imagem para 'Imagens' pois resultado foi 'Outros'.")
                classified_category = "Imagens"
                classification_method_used = "image_ocr_fallback_to_images_cat"

        if text_content:
            extracted_dates = extract_dates(text_content)
            unique_sorted_dates_str = sorted(list(set(d.strftime('%d/%m/%Y') for d in extracted_dates if d)), 
                                            key=lambda x_date: dateparser.parse(x_date, date_formats=['%d/%m/%Y']).toordinal() if dateparser.parse(x_date, date_formats=['%d/%m/%Y']) else 0)
            date_str = ", ".join(unique_sorted_dates_str) if unique_sorted_dates_str else "Nenhuma"

        if classified_category not in categories_dict and classified_category != "Outros (Não processável)":
            print(f"  AVISO: Categoria final '{classified_category}' inválida para '{filename}'. Método original: '{classification_method_used}'. Usando 'Outros'.")
            classified_category = "Outros"
            classification_method_used += "_final_invalid_cat_fallback"
        
        print(f"  Resultado Final para '{filename}': Categoria='{classified_category}', Método='{classification_method_used}', Datas='{date_str}'")
        files_to_organize.append((filename, classified_category, date_str, classification_method_used))
        if classified_category not in organized_structure: organized_structure[classified_category] = []
        organized_structure[classified_category].append(filename)
        if progress_callback: progress_callback(i + 1, total_files)

    for cat_name_key in categories_dict.keys():
        if cat_name_key not in organized_structure: organized_structure[cat_name_key] = []
    if "Outros (Não processável)" not in organized_structure and any(f_info[1] == "Outros (Não processável)" for f_info in files_to_organize):
        organized_structure["Outros (Não processável)"] = [f_info[0] for f_info in files_to_organize if f_info[1] == "Outros (Não processável)"]

    return files_to_organize, organized_structure, gemini_api_calls_count