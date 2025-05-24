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

import sys
import os

def extract_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception:
        return ""

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

def extract_text_from_file(file_path):
    extension = file_path.split('.')[-1].lower()
    
    try:
        if extension == 'pdf':
            return extract_from_pdf(file_path)
        elif extension == 'docx':
            return extract_from_docx(file_path)
        elif extension == 'txt':
            return extract_from_txt(file_path)
        elif extension in ['jpg', 'jpeg', 'png', 'bmp']:
            return extract_from_image(file_path)
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

if getattr(sys, 'frozen', False):
    model_path = os.path.join(sys._MEIPASS, MODEL_SUBFOLDER)
else:
    model_path = MODEL_NAME 

try:
    model_sbert = SentenceTransformer(model_path)
except Exception as e:
    print(f"Erro fatal ao carregar o modelo de linguagem: {e}")
    print(f"Verifique se o diretório '{model_path}' existe e contém o modelo. Se for um executável, certifique-se que o PyInstaller incluiu a pasta com --add-data.")
    sys.exit(1)

# --- Funções de Classificação (adaptada para usar a similaridade) ---
def classify_content_local(text, current_categories_dict):
    text_embedding = model_sbert.encode(text, convert_to_tensor=True)
    
    max_similarity = -1
    best_category = "Outros"
    
    for category_name, description in current_categories_dict.items():
        if not description: 
            continue
        description_embedding = model_sbert.encode(description, convert_to_tensor=True)
        similarity = util.cos_sim(text_embedding, description_embedding)
        
        if similarity > max_similarity:
            max_similarity = similarity
            best_category = category_name
            
    return None, best_category

# --- Simulação de Organização ---
def simulate_organization(folder_path, categories_dict, progress_callback=None):
    files_to_organize = []
    organized_structure = {}

    files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    total_files = len(files_in_folder)
    if total_files == 0:
        if progress_callback:
            progress_callback(1, 1) # Completa a barra se não houver arquivos
        return files_to_organize, organized_structure

    for i, filename in enumerate(files_in_folder):
        file_path = os.path.join(folder_path, filename)
        text_content = extract_text_from_file(file_path)

        if not text_content or "Formato de arquivo não suportado" in text_content:
            if "Outros" not in organized_structure:
                organized_structure["Outros"] = []
            organized_structure["Outros"].append(f"{filename} (Não processável)")
            
            if progress_callback:
                progress_callback(i + 1, total_files)
            continue

        _, classified_category = classify_content_local(text_content, categories_dict)
        dates = extract_dates(text_content)
        date_str = ", ".join([d.strftime('%d/%m/%Y') for d in dates if d]) if dates else "Nenhuma"

        files_to_organize.append((filename, classified_category, date_str))

        if classified_category not in organized_structure:
            organized_structure[classified_category] = []
        organized_structure[classified_category].append(filename)
        
        # Atualiza a barra de progresso após processar cada arquivo
        if progress_callback:
            progress_callback(i + 1, total_files)
            
    for cat in categories_dict.keys():
        if cat not in organized_structure:
            organized_structure[cat] = []

    return files_to_organize, organized_structure