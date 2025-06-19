import subprocess
import sys
import os
import shutil
import re
import dateparser
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
import time
import base64
import hashlib

# Patch para PyInstaller
if sys.platform == "win32" and getattr(sys, 'frozen', False):
    _original_Popen = subprocess.Popen
    def _patched_popen(*args, **kwargs):
        if 'creationflags' not in kwargs: kwargs['creationflags'] = 0
        kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
        return _original_Popen(*args, **kwargs)
    subprocess.Popen = _patched_popen


def get_app_data_path():
    """Cria e retorna o caminho para a pasta de dados do DocuSmart no diretório do usuário."""
    app_name = "DocuSmart"
    if sys.platform == "win32":
        path = os.path.join(os.getenv('APPDATA'), app_name)
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser('~/Library/Application Support'), app_name)
    else:
        path = os.path.join(os.path.expanduser('~/.config'), app_name)
    os.makedirs(path, exist_ok=True)
    return path


def get_file_hash(file_path):
    """Calcula o hash SHA-256 de um arquivo de forma eficiente."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Não foi possível calcular o hash para {os.path.basename(file_path)}: {e}")
        return None


def load_cache(user_id):
    """Carrega o arquivo de cache JSON para um usuário específico."""
    cache_path = os.path.join(get_app_data_path(), f"cache_{user_id}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(user_id, cache_data):
    """Salva o dicionário de cache em um arquivo JSON para um usuário específico."""
    cache_path = os.path.join(get_app_data_path(), f"cache_{user_id}.json")
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=4)
    except IOError as e:
        print(f"Erro ao salvar o cache para o usuário {user_id}: {e}")



def get_tesseract_path():
    """Retorna o caminho para o executável do Tesseract de acordo com o SO."""
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    if sys.platform == "win32":
        return os.path.join(base_path, 'tesseract', 'tesseract.exe')
    elif sys.platform in ["linux", "darwin"]:
        return os.path.join(base_path, 'tesseract', 'tesseract')
    else:
        raise OSError(f"Sistema operacional não suportado para Tesseract: {sys.platform}")


def get_poppler_path():
    """Retorna o caminho para a pasta 'bin' do Poppler de acordo com o SO."""
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    if sys.platform == "win32":
        return os.path.join(base_path, 'poppler-24.08.0', 'Library', 'bin')
    elif sys.platform == "darwin":
        return os.path.join(base_path, 'poppler', 'bin')
    elif sys.platform == "linux":
        return os.path.join(base_path, 'poppler', 'bin')
    else:
        raise OSError(f"Sistema operacional não suportado para Poppler: {sys.platform}")

# def get_tesseract_path():
#     base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
#     return os.path.join(base_path, 'tesseract', 'tesseract.exe')

def configure_tesseract():
    tess_path = get_tesseract_path()
    tessdata_path = os.path.join(os.path.dirname(tess_path), 'tessdata')
    pytesseract.pytesseract.tesseract_cmd = tess_path
    os.environ['TESSDATA_PREFIX'] = tessdata_path

# def get_poppler_path():
#     base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
#     return os.path.join(base_path, 'poppler-24.08.0', 'Library', 'bin')

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
    max_slides_to_process = 50 
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
    sys.exit("Falha ao carregar modelo SBERT. O aplicativo não pode continuar.")


def classify_content_local(text, categories_embeddings_dict):
    if not text or len(text.strip()) < 5: return "Outros", 0.0 
    text_embedding = model_sbert.encode(text, convert_to_tensor=True)
    max_similarity, best_category = -1.0, "Outros"
    for category_name, description_embedding in categories_embeddings_dict.items():
        if description_embedding is None: continue
        similarity = util.cos_sim(text_embedding, description_embedding).item()
        if similarity > max_similarity:
            max_similarity, best_category = similarity, category_name
    return best_category, (max_similarity + 1) / 2


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


def classify_text_gemini_via_edge(text_content, categories_dict):
    if not config.supabase:
        print("ERRO: Cliente Supabase não inicializado em config.py.")
        return "Outros", 0.0
    if not text_content or len(text_content.strip()) < 10:
        print("Texto muito curto para enviar para Edge Function, retornando 'Outros'.")
        return "Outros", 0.0

    print(text_content)
    function_name = "classify-document-gemini"
    payload = {"document_text": text_content, "categories": categories_dict}

    max_retries = 4
    base_delay_seconds = 2

    for attempt in range(max_retries):
        try:
            print(f"Invocando Edge Function '{function_name}' (Tentativa {attempt + 1})...")

            response_from_invoke = config.supabase.functions.invoke(function_name, invoke_options={'body': payload})

            processed_data = None
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
            if hasattr(e, 'status') and e.status == 429:
                delay = base_delay_seconds * (2 ** attempt)
                print(f"--- Limite de taxa (RPM) atingido. Tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s... ---")
                time.sleep(delay)
            else:
                print(f"Erro de API não recuperável ({getattr(e, 'status', 'N/A')}): {e.message}")
                return "Outros", 0.0

        except Exception as e:
            print(f"Erro crítico ao invocar Edge Function '{function_name}': {type(e).__name__} - {e}")
            return "Outros", 0.0

    print(f"Número máximo de retentativas ({max_retries}) atingido. Desistindo deste arquivo.")
    return "Outros", 0.0


def classify_document_file_via_edge(file_path, categories_dict):
    if not config.supabase:
        print("ERRO: Cliente Supabase não inicializado.")
        return "Outros", 0.0

    function_name = "classify-document-file"
    max_retries = 4
    base_delay_seconds = 2

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
        
        extension = os.path.splitext(file_path)[1].lower().replace(".", "")
        image_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff']
        mime_type = f'image/{extension}' if extension in image_extensions else f'application/{extension}'
        
        payload = {
            "file_data_base64": base64_encoded_data,
            "mime_type": mime_type,
            "categories": categories_dict
        }
    except Exception as e:
        print(f"Erro ao ler e codificar o arquivo '{os.path.basename(file_path)}': {e}")
        return "Outros", 0.0

    for attempt in range(max_retries):
        try:
            print(f"Invocando Edge Function '{function_name}' (Tentativa {attempt + 1})...")
            response = config.supabase.functions.invoke(function_name, invoke_options={'body': payload})
            
            processed_data = json.loads(response.decode('utf-8')) if isinstance(response, bytes) else response

            if isinstance(processed_data, dict) and "category" in processed_data:
                print("Resposta da Edge Function (Arquivo) processada com sucesso.")
                return processed_data.get("category", "Outros"), processed_data.get("confidence", 0.3)
            else:
                print(f"ERRO: Resposta da Edge Function (Arquivo) em formato inesperado: {processed_data}")
                return "Outros", 0.0

        except APIError as e:
            if hasattr(e, 'status') and e.status == 429:
                delay = base_delay_seconds * (2 ** attempt)
                print(f"--- Limite de taxa (RPM) atingido. Tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s... ---")
                time.sleep(delay)
            else:
                print(f"Erro de API não recuperável ({getattr(e, 'status', 'N/A')}): {e.message}")
                return "Outros", 0.0
        except Exception as e:
            print(f"Erro ao calcular similaridade local: {e}")
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
    user_id = config.current_user.id if config.current_user else "local_user"
    cache_data = load_cache(user_id)
    cache_was_updated = False

    categories_embeddings_dict = {}
    if not use_gemini or (use_gemini and available_credits_for_simulation == 0):
        print("Modo Local ou fallback: Pré-calculando embeddings SBERT...")
        for category_name, description in categories_dict.items():
            if description and category_name != "Outros (Não processável)":
                categories_embeddings_dict[category_name] = model_sbert.encode(description, convert_to_tensor=True)
            else:
                categories_embeddings_dict[category_name] = None
        print("Embeddings SBERT das categorias pré-calculados.")

    files_to_organize = []
    organized_structure = {}
    gemini_api_calls_count = 0

    try:
        files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except FileNotFoundError:
        return [], {}, 0
        
    total_files = len(files_in_folder)
    if total_files == 0:
        return [], {}, 0

    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'] 

    for i, filename in enumerate(files_in_folder):
        file_path = os.path.join(folder_path, filename)
        file_hash = get_file_hash(file_path)
        if file_hash and file_hash in cache_data:
            print(f"\nProcessando: {filename} (Resultado encontrado no cache!)")
            classified_category = cache_data[file_hash]
            classification_method_used = "cache"
            date_str = "N/A (cache)"

            try:
                text_for_dates = extract_text_from_file(file_path)
                if text_for_dates:
                    dates_list = extract_dates(text_for_dates)
                    date_str = ", ".join(dates_list) if dates_list else "Nenhuma"
            except Exception:
                pass

            files_to_organize.append((filename, classified_category, date_str, classification_method_used))
            if classified_category not in organized_structure: organized_structure[classified_category] = []
            organized_structure[classified_category].append(filename)
            if progress_callback: progress_callback(i + 1, total_files)
            continue

        extension = os.path.splitext(filename)[1].lower()
        classified_category = "Outros"
        classification_method_used = "fallback_initial"
        date_str = "Nenhuma"

        print(f"\nProcessando: {filename}")

        if use_gemini and gemini_api_calls_count < available_credits_for_simulation:
            gemini_category, _ = classify_document_file_via_edge(file_path, categories_dict)
            classification_method_used = "gemini_file_upload"
            
            if gemini_category and gemini_category != "Outros":
                gemini_api_calls_count += 1
            classified_category = gemini_category
        else:
            if use_gemini:
                classification_method_used = "local_due_to_no_credits"
            else:
                classification_method_used = "local_explicit_choice"

            text_content = extract_text_from_file(file_path)

            if text_content == "Formato de arquivo não suportado.":
                classified_category = "Outros (Não processável)"
            elif extension in image_extensions and not text_content:
                classified_category = "Imagens"
            else:
                kw_category, kw_conf = classify_by_filename_keywords(filename, categories_dict)
                if kw_conf > 0.95:
                    classified_category = kw_category
                    classification_method_used += "_keyword"
                else:
                    sbert_category, _ = classify_content_local(text_content, categories_embeddings_dict)
                    classified_category = sbert_category
                    classification_method_used += "_sbert"

        if file_hash and classification_method_used.startswith("gemini"):
            cache_data[file_hash] = classified_category
            cache_was_updated = True
            print(f"  Resultado salvo no cache para '{filename}'.")

        final_text_for_dates = extract_text_from_file(file_path)
        if final_text_for_dates:
            dates_list = extract_dates(final_text_for_dates)
            date_str = ", ".join(dates_list) if dates_list else "Nenhuma"

        if classified_category not in categories_dict and classified_category != "Outros (Não processável)":
            classified_category = "Outros"
        
        print(f"  Resultado Final para '{filename}': Categoria='{classified_category}', Método='{classification_method_used}'")
        files_to_organize.append((filename, classified_category, date_str, classification_method_used))
        if classified_category not in organized_structure: organized_structure[classified_category] = []
        organized_structure[classified_category].append(filename)
        if progress_callback: progress_callback(i + 1, total_files)

    if cache_was_updated:
        print("Salvando novas entradas no arquivo de cache...")
        save_cache(user_id, cache_data)

    for cat_name_key in categories_dict.keys():
        if cat_name_key not in organized_structure: organized_structure[cat_name_key] = []
    
    return files_to_organize, organized_structure, gemini_api_calls_count