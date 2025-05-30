import subprocess
import sys
import os


if sys.platform == "win32" and getattr(sys, 'frozen', False):
    _original_Popen = subprocess.Popen

    def _patched_Popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = 0
        kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
        return _original_Popen(*args, **kwargs)
    subprocess.Popen = _patched_Popen


import customtkinter as ctk
import os
import shutil
import re
import dateparser
from PyPDF2 import PdfReader
import docx
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util
import CTkMessagebox
import cv2
import numpy as np
from pdf2image import convert_from_path
import fitz
import openpyxl
from pptx import Presentation
from bs4 import BeautifulSoup


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


def get_poppler_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, 'poppler-24.08.0', 'Library', 'bin')


def preprocess_image(pil_image):
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)


def extract_from_pdf(file_path):
    text = ""
    max_pages = 15
    try:
        doc = fitz.open(file_path)
        num_pages_to_process = min(doc.page_count, max_pages)
        for i in range(num_pages_to_process):
            page = doc.load_page(i)
            text += page.get_text()
        doc.close()

        if len(text.strip()) < 50:
            images = convert_from_path(file_path, poppler_path=get_poppler_path(), dpi=300)
            ocr_text_accumulator = ""
            for i, image in enumerate(images):
                preprocessed_image = preprocess_image(image)
                page_ocr_text = pytesseract.image_to_string(preprocessed_image, lang='por+eng')
                if page_ocr_text:
                    ocr_text_accumulator += f"\n--- OCR Page {i+1} ---\n" + page_ocr_text + "\n"

            if len(ocr_text_accumulator.strip()) > len(text.strip()):
                text = ocr_text_accumulator
            else:
                text += ocr_text_accumulator
    except Exception:
        return ""
    return text.strip()


def extract_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception:
        return ""


def extract_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""


def extract_from_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return ""


def extract_from_pptx(file_path: str) -> str:
    text = []
    try:
        prs = Presentation(file_path)
        for i, slide in enumerate(prs.slides):
            text.append(f"--- Slide {i+1} ---")
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text).strip()
    except Exception:
        return ""


def extract_from_html(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text.strip()
    except Exception:
        return ""


def extract_text_from_file(file_path):
    extension = file_path.split('.')[-1].lower()
    print(f"Arquivo: {file_path}, extensão: {extension}")
    try:
        if extension == 'pdf':
            return extract_from_pdf(file_path)
        elif extension == 'docx':
            return extract_from_docx(file_path)
        elif extension == 'txt':
            return extract_from_txt(file_path)
        elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            return extract_from_image(file_path)
        elif extension == 'xlsx':
            return extract_from_xlsx(file_path)
        elif extension == 'pptx':
            return extract_from_pptx(file_path)
        elif extension == 'html':
            return extract_from_html(file_path)
        else:
            return "Formato de arquivo não suportado."
    except Exception as e:
        return str(e)


def extract_dates(text):
    pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    dates = re.findall(pattern, text)
    return [dateparser.parse(d) for d in dates if dateparser.parse(d)]


MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2' # Ou 'all-MiniLM-L6-v2'
MODEL_SUBFOLDER = os.path.join('modelos', MODEL_NAME)

configure_tesseract()

if getattr(sys, 'frozen', False):
    model_path = os.path.join(sys._MEIPASS, MODEL_SUBFOLDER)
else:
    model_path = MODEL_SUBFOLDER

try:
    model_sbert = SentenceTransformer(model_path)
except Exception as e:
    print(f"Erro fatal ao carregar o modelo de linguagem: {e}")
    print(f"Verifique se o diretório '{model_path}' existe e contém o modelo. Se for um executável, certifique-se que o PyInstaller incluiu a pasta com --add-data.")
    sys.exit(1)


def classify_content_local(text, categories_embeddings_dict):
    if not text:
        return 0.0, "Outros"

    try:
        text_embedding = model_sbert.encode(text, convert_to_tensor=True)
    except Exception as e:
        print(f"Erro ao codificar o texto '{text[:50]}...': {e}")
        return 0.0, "Outros"

    max_similarity = -1.0
    best_category = "Outros"

    for category_name, description_embedding in categories_embeddings_dict.items():
        if description_embedding is None:
            continue

        try:
            similarity = util.cos_sim(text_embedding, description_embedding).item()
        except Exception as e:
            print(f"Erro ao calcular similaridade para categoria '{category_name}': {e}")
            continue

        if similarity > max_similarity:
            max_similarity = similarity
            best_category = category_name
    
    return max_similarity, best_category


def classify_by_filename_keywords(filename):
    clean_filename = os.path.splitext(filename)[0].lower()

    if re.search(r'extrato|fatura|boleto|conta|holerite|imposto|recibo', clean_filename):
        return "Financeiro", 1.0
    elif re.search(r'rg|cpf|cnh|passaporte|certidao|eleitor|nascimento|casamento|identidade', clean_filename):
        return "Pessoal", 1.0
    elif re.search(r'contrato|peticao|notificacao|judicial|acordo|escritura', clean_filename):
        return "Jurídico", 1.0
    elif re.search(r'exame|laudo|receita|medico|vacina|consulta|historico|saude', clean_filename):
        return "Saúde", 1.0
    return "Outros", 0.0


def simulate_organization(folder_path, categories_dict, progress_callback=None):
    categories_embeddings_dict = {}
    print("Pré-calculando embeddings das descrições das categorias...")
    for category_name, description in categories_dict.items():
        if description:
            try:
                categories_embeddings_dict[category_name] = model_sbert.encode(description, convert_to_tensor=True)
            except Exception as e:
                print(f"Erro ao codificar descrição da categoria '{category_name}': {e}")
                categories_embeddings_dict[category_name] = None
        else:
            categories_embeddings_dict[category_name] = None
    print("Embeddings das categorias pré-calculados.")

    files_to_organize = []
    organized_structure = {}

    files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    total_files = len(files_in_folder)
    if total_files == 0:
        if progress_callback:
            progress_callback(1, 1)
        return files_to_organize, organized_structure

    image_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff']

    TITLE_KEYWORD_CONFIDENCE = 0.9
    TITLE_SBERT_THRESHOLD = 0.7
    CONTENT_SBERT_THRESHOLD = 0.4

    for i, filename in enumerate(files_in_folder):
        file_path = os.path.join(folder_path, filename)
        extension = filename.split('.')[-1].lower()
        text_content = extract_text_from_file(file_path)

        classified_category = "Outros"

        if extension in image_extensions:
            classified_category = "Imagens"
            text_content = None

        if classified_category == "Outros":
            title_keyword_category, keyword_confidence = classify_by_filename_keywords(filename)
            print(f"Palavra-chave: {title_keyword_category}, Confiança: {keyword_confidence}")

            if keyword_confidence >= TITLE_KEYWORD_CONFIDENCE:
                classified_category = title_keyword_category
            else:
                clean_filename = os.path.splitext(filename)[0]
                title_sbert_similarity, title_sbert_category = classify_content_local(clean_filename, categories_embeddings_dict)

                content_sbert_similarity, content_sbert_category = (0, "Outros")
                if text_content and "Formato de arquivo não suportado" not in text_content:
                    content_sbert_similarity, content_sbert_category = classify_content_local(text_content, categories_embeddings_dict)
                
                print(f"Conteúdo SBERT Similaridade: {content_sbert_similarity}, Categoria: {content_sbert_category}")
                print(f"Título SBERT Similaridade: {title_sbert_similarity}, Categoria: {title_sbert_category}")

                if content_sbert_similarity >= CONTENT_SBERT_THRESHOLD and (title_sbert_similarity < TITLE_SBERT_THRESHOLD or content_sbert_similarity > title_sbert_similarity):
                    classified_category = content_sbert_category
                    print("AAAAAAAAAAA - Conteúdo acima do threshold e prevaleceu")
                elif title_sbert_similarity >= TITLE_SBERT_THRESHOLD:
                    classified_category = title_sbert_category
                    print("BBBBBBBBB - Título acima do threshold")
                else:
                    classified_category = "Outros"
                    print("Sem classificação SBERT acima do threshold, mantendo 'Outros'")
        print("\n")

        dates = extract_dates(text_content)
        date_str = ", ".join([d.strftime('%d/%m/%Y') for d in dates if d]) if dates else "Nenhuma"

        files_to_organize.append((filename, classified_category, date_str))

        if classified_category not in organized_structure:
            organized_structure[classified_category] = []
        organized_structure[classified_category].append(filename)

        if progress_callback:
            progress_callback(i + 1, total_files)

    for cat in categories_dict.keys():
        if cat not in organized_structure:
            organized_structure[cat] = []

    return files_to_organize, organized_structure