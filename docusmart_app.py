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
import organizer
import threading

# --- Configuração do Modelo de Linguagem (com ajuste para PyInstaller) ---
import sys
import os

# --- Classe Principal do Aplicativo ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DocuSmart - Organizador de Documentos")
        self.geometry("900x700")
        
        self.big_font = ctk.CTkFont(family="Arial", size=18, weight="bold")
        self.medium_font = ctk.CTkFont(family="Arial", size=16)
        self.small_font = ctk.CTkFont(family="Arial", size=14)
        
        self.primary_color = "#3498db"
        self.secondary_color = "#2ecc71"
        self.cancel_color = "#e74c3c"
        self.text_color = "#2c3e50"
        self.bg_color = "#ecf0f1"
        self.frame_color = "#ffffff"
        # Cores para o log
        self.log_bg_color = "#f8f8f8" # Um cinza bem claro, quase branco
        self.log_text_color = "#333333" # Um cinza escuro para o texto

        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1) 

        self.default_categories = {
            "Pessoal": "Documentos de identificação e registro civil, como RG (Registro Geral), CPF (Cadastro de Pessoa Física), CNH (Carteira Nacional de Habilitação), certidão de nascimento, certidão de casamento, passaporte, título de eleitor. Inclui também fotografias e outros registros pessoais de caráter não profissional ou financeiro.",
            "Saúde": "Registros e informações médicas, como resultados de exames laboratoriais (sangue, urina, imagem como raio-x, ultrassom, ressonância), laudos médicos, receitas de medicamentos, atestados médicos, relatórios de consultas, histórico de vacinação e comprovantes de planos de saúde ou despesas médicas.",
            "Finanças": "Comprovantes e extratos relacionados a transações monetárias e obrigações financeiras. Exemplos incluem boletos bancários, contas de consumo (água, luz, gás, telefone, internet), faturas de cartão de crédito, extratos bancários, comprovantes de pagamento, holerites (contracheques), declarações de imposto de renda e comprovantes de investimentos.",
            "Acadêmico": "Material educacional e documentos de formação. Isso abrange diplomas de graduação ou pós-graduação, certificados de cursos (livres, técnicos, extensão), histórico escolar ou acadêmico, anotações de aula, trabalhos de faculdade, artigos científicos, apostilas e comprovantes de matrícula ou conclusão de estudos.",
            "Outros": "Documentos que não se encaixam claramente nas categorias anteriores ou que possuem um propósito muito diverso. Inclui arquivos temporários, downloads variados, documentos sem identificação clara de tema, ou itens que aguardam uma classificação manual."
        }
        self.current_categories = self.default_categories.copy()

        self.control_frame = ctk.CTkFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.control_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=0)

        self.instruction_label = ctk.CTkLabel(
            self.control_frame,
            text="Passo 1: Selecione a pasta com seus documentos para organizar.",
            font=self.big_font,
            text_color=self.text_color
        )
        self.instruction_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")


        self.select_folder_button = ctk.CTkButton(
            self.control_frame,
            text="📂 Selecionar Pasta",
            command=self.select_folder,
            font=self.medium_font,
            fg_color=self.primary_color,
            hover_color="#2980b9"
        )
        self.select_folder_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.selected_folder_path = ctk.CTkLabel(
            self.control_frame,
            text="Nenhuma pasta selecionada.",
            font=self.small_font,
            text_color=self.text_color,
            wraplength=500
        )
        self.selected_folder_path.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.instruction_label_2 = ctk.CTkLabel(
            self.control_frame,
            text="Passo 2: Verifique e gerencie suas categorias.",
            font=self.big_font,
            text_color=self.text_color
        )
        self.instruction_label_2.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        self.manage_categories_button = ctk.CTkButton(
            self.control_frame,
            text="⚙️ Gerenciar Categorias",
            command=self.open_category_manager,
            font=self.medium_font,
            fg_color=self.primary_color,
            hover_color="#2980b9"
        )
        self.manage_categories_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.instruction_label_3 = ctk.CTkLabel(
            self.control_frame,
            text="Passo 3: Visualize e confirme a organização.",
            font=self.big_font,
            text_color=self.text_color
        )
        self.instruction_label_3.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")


        self.preview_organize_button = ctk.CTkButton(
            self.control_frame,
            text="🔍 Visualizar Organização",
            command=self.show_organization_preview,
            state="disabled",
            font=self.big_font,
            fg_color=self.secondary_color,
            hover_color="#27ae60"
        )
        self.preview_organize_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        # BARRA DE PROGRESSO
        self.progress_bar = ctk.CTkProgressBar(
            self.control_frame, 
            orientation="horizontal", 
            mode="determinate", 
            height=20, 
            corner_radius=5,
            fg_color="#ecf0f1", # Cor de fundo da barra
            progress_color="#2f714b" # Cor do preenchimento da barra
        )
        self.progress_bar.grid(row=7, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0) # Inicializa a barra em 0
        self.progress_bar.grid_remove() # Esconde a barra inicialmente

        # LABEL DE STATUS DA BARRA DE PROGRESSO
        self.progress_label = ctk.CTkLabel(
            self.control_frame,
            text="Aguardando...",
            font=self.small_font,
            text_color=self.text_color
        )
        self.progress_label.grid(row=8, column=0, padx=10, pady=2, sticky="w")
        self.progress_label.grid_remove() # Esconde o label inicialmente

        # Área de log/status
        self.log_textbox = ctk.CTkTextbox(self, width=600, height=300, 
                                        font=self.small_font, 
                                        text_color=self.log_text_color, # Cor do texto do log
                                        fg_color=self.log_bg_color) # Cor de fundo do log
        self.log_textbox.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        self.log_textbox.insert("end", "Bem-vindo ao DocuSmart!\nSiga os passos acima para organizar seus documentos.\n")
        self.log_textbox.configure(state="disabled")

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        # Adicionar uma linha extra de quebra para dar mais espaçamento visual
        self.log_textbox.insert("end", message + "\n\n") 
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def update_progress(self, current, total):
        # Esta função será chamada pelo thread de simulação/organização
        # Usamos after para garantir que a atualização da UI ocorra no thread principal
        self.after(10, lambda: self._update_progress_ui(current, total))

    def _update_progress_ui(self, current, total):
        if total > 0:
            progress_value = current / total
            self.progress_bar.set(progress_value)
            self.progress_label.configure(text=f"Processando {current}/{total} arquivos...")
            self.update_idletasks() # Força a atualização da UI

    def select_folder(self):
        folder_selected = ctk.filedialog.askdirectory()
        if folder_selected:
            self.selected_folder_path.configure(text=f"Pasta selecionada: {folder_selected}")
            self.folder_to_organize = folder_selected
            self.preview_organize_button.configure(state="normal")
            self.log_message(f"Pasta '{folder_selected}' selecionada com sucesso.")
            # Esconde a barra de progresso e o label ao selecionar uma nova pasta
            self.progress_bar.grid_remove()
            self.progress_label.grid_remove()
            self.progress_bar.set(0) # Reseta o progresso
            self.progress_label.configure(text="Aguardando...")

        else:
            self.selected_folder_path.configure(text="Nenhuma pasta selecionada.")
            self.preview_organize_button.configure(state="disabled")
            self.log_message("Seleção de pasta cancelada.")
            self.progress_bar.grid_remove()
            self.progress_label.grid_remove()

    def show_organization_preview(self):
        if not hasattr(self, 'folder_to_organize') or not self.folder_to_organize:
            self.log_message("Erro: Nenhuma pasta foi selecionada para organizar.")
            return
        
        if not self.current_categories or len(self.current_categories) == 0:
            self.log_message("Erro: Nenhuma categoria definida. Por favor, defina suas categorias antes de visualizar a organização.")
            return

        self.log_message("Simulando organização para prévia...")
        self.preview_organize_button.configure(state="disabled")
        self.select_folder_button.configure(state="disabled") # Desabilita outros botões
        self.manage_categories_button.configure(state="disabled")


        # Mostra a barra de progresso e o label
        self.progress_bar.grid()
        self.progress_label.grid()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando processamento de arquivos...")
        self.update_idletasks() # Força a atualização para exibir a barra

        # Usa threading para não congelar a UI durante a simulação
        self.simulation_thread = threading.Thread(target=self._run_simulation_in_thread)
        self.simulation_thread.start()

    def _run_simulation_in_thread(self):
        # Esta função roda em um thread separado
        files_info, structure_info = organizer.simulate_organization(
            self.folder_to_organize, 
            self.current_categories, 
            self.update_progress # Passa a função de callback para o organizer
        )
        
        # Volta para o thread principal para atualizar a UI após a simulação
        self.after(100, lambda: self._post_simulation_ui_update(files_info, structure_info))

    def _post_simulation_ui_update(self, files_info, structure_info):
        # Esconde a barra de progresso e o label após a simulação
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        self.progress_bar.set(0) # Reseta o progresso
        self.progress_label.configure(text="Aguardando...")

        if not files_info and not structure_info:
            self.log_message("Nenhum arquivo processável encontrado na pasta.")
            self.preview_organize_button.configure(state="normal")
            self.select_folder_button.configure(state="normal") # Reabilita botões
            self.manage_categories_button.configure(state="normal")
            return

        preview_window = OrganizationPreview(self, files_info, structure_info)
        preview_window.grab_set()
        self.wait_window(preview_window) # Espera a janela de prévia fechar

        if hasattr(preview_window, 'confirmed') and preview_window.confirmed:
            self.log_message("Prévia confirmada. Iniciando organização real...")
            self._execute_organization_real(files_info)
        else:
            self.log_message("Organização cancelada pelo usuário ou janela fechada.")
        
        self.preview_organize_button.configure(state="normal")
        self.select_folder_button.configure(state="normal") # Reabilita botões
        self.manage_categories_button.configure(state="normal")

    def _execute_organization_real(self, files_info):
        self.log_message("Iniciando a movimentação dos arquivos...")
        
        # Mostra a barra de progresso novamente para a organização real
        self.progress_bar.grid()
        self.progress_label.grid()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Movendo arquivos...")
        self.update_idletasks()

        total_files_to_move = len(files_info)
        if total_files_to_move == 0:
            self.log_message("Nenhum arquivo para mover.")
            self.progress_bar.grid_remove()
            self.progress_label.grid_remove()
            return

        for i, (filename, classified_category, _) in enumerate(files_info):
            original_file_path = os.path.join(self.folder_to_organize, filename)
            
            if "Não processável" in classified_category:
                self.log_message(f"Pulando '{filename}' (Não processável).")
                self.update_progress(i + 1, total_files_to_move) # Atualiza o progresso mesmo para pulados
                continue

            target_category_path = os.path.join(self.folder_to_organize, classified_category)

            if not os.path.exists(target_category_path):
                os.makedirs(target_category_path)
                self.log_message(f"Criando pasta: '{classified_category}'")

            try:
                shutil.move(original_file_path, os.path.join(target_category_path, filename))
                self.log_message(f"Arquivo '{filename}' movido para '{classified_category}'.")
            except Exception as e:
                self.log_message(f"Erro ao mover '{filename}': {e}")
            
            self.update_progress(i + 1, total_files_to_move) # Atualiza o progresso

        self.log_message("Organização finalizada com sucesso!")
        self.progress_bar.grid_remove() # Esconde a barra de progresso
        self.progress_label.grid_remove() # Esconde o label de progresso
        self.progress_bar.set(0) # Reseta o progresso
        self.progress_label.configure(text="Aguardando...")

    def open_category_manager(self):
        category_manager_window = CategoryManager(self)
        category_manager_window.grab_set()
        self.wait_window(category_manager_window)

        if hasattr(category_manager_window, 'result_categories'):
            self.current_categories = category_manager_window.result_categories
            self.log_message("Categorias atualizadas pelo usuário.")

# --- Classe para Gerenciamento de Categorias (com aprimoramentos visuais) ---
class CategoryManager(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Gerenciar Categorias de Documentos")
        self.geometry("800x650")
        self.resizable(False, False)

        self.master = master
        self.current_categories = master.current_categories.copy()
        self.original_categories = master.current_categories.copy()

        self.big_font = master.big_font
        self.medium_font = master.medium_font
        self.small_font = master.small_font
        self.primary_color = master.primary_color
        self.secondary_color = master.secondary_color
        self.cancel_color = master.cancel_color
        self.text_color = master.text_color
        self.bg_color = master.bg_color
        self.frame_color = master.frame_color
        
        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)


        ctk.CTkLabel(self, text="Defina ou Edite Suas Categorias de Documentos", 
                    font=self.big_font, text_color=self.text_color).grid(row=0, column=0, padx=20, pady=10)

        self.category_list_frame = ctk.CTkScrollableFrame(self, label_text="Categorias Atuais e Descrições (editável)", 
                                                        height=300, fg_color=self.frame_color, corner_radius=10,
                                                        label_font=self.medium_font) # Removido text_color daqui
        self.category_list_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.category_list_frame.grid_columnconfigure(0, weight=1)
        self.category_list_frame.grid_columnconfigure(1, weight=2)
        self.category_list_frame.grid_columnconfigure(2, weight=0)

        self.category_widgets = {}

        self.load_categories_to_display()

        self.add_category_frame = ctk.CTkFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.add_category_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.add_category_frame.grid_columnconfigure(0, weight=1)
        self.add_category_frame.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(self.add_category_frame, text="✨ Adicionar Nova Categoria:", font=self.medium_font, text_color=self.text_color).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.add_category_frame, text="Nome:", font=self.small_font, text_color=self.text_color).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.new_category_name_entry = ctk.CTkEntry(self.add_category_frame, placeholder_text="Ex: Contratos", font=self.small_font)
        self.new_category_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.add_category_frame, text="Descrição:", font=self.small_font, text_color=self.text_color).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.new_category_description_entry = ctk.CTkEntry(self.add_category_frame, placeholder_text="Ex: Acordos legais, termos de serviço", font=self.small_font)
        self.new_category_description_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.add_category_button = ctk.CTkButton(self.add_category_frame, text="➕ Adicionar", 
                                                command=self.add_new_category, font=self.medium_font,
                                                fg_color=self.primary_color, hover_color="#2980b9")
        self.add_category_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        self.action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.action_buttons_frame.grid_columnconfigure((0,1,2), weight=1)

        self.reset_button = ctk.CTkButton(self.action_buttons_frame, text="🔄 Redefinir para Padrão", 
                                        command=self.reset_categories, font=self.medium_font,
                                        fg_color="gray", hover_color="darkgray")
        self.reset_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.save_button = ctk.CTkButton(self.action_buttons_frame, text="✅ Salvar e Fechar", 
                                        command=self.save_and_close, font=self.medium_font,
                                        fg_color=self.secondary_color, hover_color="#27ae60")
        self.save_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        self.cancel_button = ctk.CTkButton(self.action_buttons_frame, text="❌ Cancelar", 
                                        command=self.destroy, font=self.medium_font,
                                        fg_color=self.cancel_color, hover_color="darkred")
        self.cancel_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

    def load_categories_to_display(self):
        for widget in self.category_list_frame.winfo_children():
            widget.destroy()
        
        self.category_widgets = {}

        row_idx = 0
        for category_name, description in self.current_categories.items():
            name_label = ctk.CTkLabel(self.category_list_frame, text=category_name, 
                                    font=self.medium_font, text_color=self.text_color)
            name_label.grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")

            description_entry = ctk.CTkEntry(self.category_list_frame, width=300, font=self.small_font)
            description_entry.insert(0, description)
            description_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")

            if category_name.lower() != "outros":
                remove_button = ctk.CTkButton(self.category_list_frame, text="Remover", 
                                                command=lambda c=category_name: self.remove_category(c),
                                                width=80, fg_color=self.cancel_color, hover_color="darkred",
                                                font=self.small_font)
                remove_button.grid(row=row_idx, column=2, padx=5, pady=5, sticky="e")
            else:
                ctk.CTkLabel(self.category_list_frame, text=" (Essencial)", 
                            font=self.small_font, text_color="gray").grid(row=row_idx, column=2, padx=5, pady=5, sticky="e")

            self.category_widgets[category_name] = {
                "name_label": name_label,
                "description_entry": description_entry
            }
            row_idx += 1
        
        if not self.current_categories:
            ctk.CTkLabel(self.category_list_frame, text="Nenhuma categoria definida. Por favor, adicione uma.", 
                        font=self.medium_font, text_color="gray").grid(row=0, column=0, columnspan=3, padx=5, pady=10)

    def add_new_category(self):
        name = self.new_category_name_entry.get().strip()
        description = self.new_category_description_entry.get().strip()

        if not name:
            CTkMessagebox.CTkMessagebox(title="Aviso", message="O nome da categoria não pode estar vazio.", icon="warning")
            return
        if name in self.current_categories:
            CTkMessagebox.CTkMessagebox(title="Aviso", message=f"A categoria '{name}' já existe.", icon="warning")
            return

        self.current_categories[name] = description
        self.new_category_name_entry.delete(0, "end")
        self.new_category_description_entry.delete(0, "end")
        self.master.log_message(f"Categoria '{name}' adicionada.")
        self.load_categories_to_display()

    def remove_category(self, category_name):
        if category_name.lower() == "outros":
            self.master.log_message("Não é possível remover a categoria 'Outros', ela é essencial.")
            return

        msg_box = CTkMessagebox.CTkMessagebox(
            title="Confirmar Exclusão",
            message=f"Tem certeza que deseja remover a categoria '{category_name}'?",
            icon="question",
            option_1="Não",
            option_2="Sim"
        )
        response = msg_box.get()

        if response == "Sim":
            del self.current_categories[category_name]
            self.master.log_message(f"Categoria '{category_name}' removida.")
            self.load_categories_to_display()

    def reset_categories(self):
        msg_box = CTkMessagebox.CTkMessagebox(
            title="Confirmar Redefinição",
            message="Tem certeza que deseja redefinir todas as categorias para as configurações padrão?",
            icon="warning",
            option_1="Não",
            option_2="Sim"
        )
        response = msg_box.get()

        if response == "Sim":
            self.current_categories = self.master.default_categories.copy()
            self.master.log_message("Categorias redefinidas para o padrão.")
            self.load_categories_to_display()

    def save_and_close(self):
        for category_name, widgets in self.category_widgets.items():
            if "description_entry" in widgets: 
                self.current_categories[category_name] = widgets["description_entry"].get().strip()
        
        if "Outros" not in self.current_categories or not self.current_categories["Outros"]:
            self.current_categories["Outros"] = self.master.default_categories.get("Outros", "documentos diversos que não se encaixam nas categorias.")

        self.result_categories = self.current_categories
        self.destroy()

# --- Classe: Janela de Prévia da Organização (com aprimoramentos visuais) ---
class OrganizationPreview(ctk.CTkToplevel):
    def __init__(self, master, files_info, structure_info):
        super().__init__(master)
        self.title("Prévia da Organização")
        self.geometry("1000x750")
        self.resizable(False, False)

        self.master = master
        self.files_info = files_info
        self.structure_info = structure_info
        self.confirmed = False

        self.big_font = master.big_font
        self.medium_font = master.medium_font
        self.small_font = master.small_font
        self.primary_color = master.primary_color
        self.secondary_color = master.secondary_color
        self.cancel_color = master.cancel_color
        self.text_color = master.text_color
        self.bg_color = master.bg_color
        self.frame_color = master.frame_color

        self.small_italic_font = ctk.CTkFont(family="Segoe UI", size=12, slant="italic")
        
        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        ctk.CTkLabel(self, text="Verifique a prévia da organização antes de confirmar:", 
                    font=self.big_font, text_color=self.text_color).grid(row=0, column=0, padx=20, pady=10)

        self.preview_frame = ctk.CTkScrollableFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.preview_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)

        self._display_preview_content()

        self.action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_buttons_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.action_buttons_frame.grid_columnconfigure((0,1), weight=1)

        self.confirm_button = ctk.CTkButton(self.action_buttons_frame, text="✅ Confirmar Organização", 
                                            command=self._confirm_organization, font=self.big_font,
                                            fg_color=self.secondary_color, hover_color="#27ae60")
        self.confirm_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.cancel_button = ctk.CTkButton(self.action_buttons_frame, text="❌ Cancelar", 
                                        command=self._cancel_organization, font=self.big_font,
                                        fg_color=self.cancel_color, hover_color="darkred")
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def _display_preview_content(self):
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        row_idx = 0
        
        ctk.CTkLabel(self.preview_frame, text="Estrutura de Pastas e Conteúdo Estimado:", 
                    font=self.medium_font, text_color=self.text_color).grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        row_idx += 1

        sorted_categories = sorted(self.structure_info.keys())

        for category in sorted_categories:
            files_in_category = self.structure_info.get(category, [])
            
            ctk.CTkLabel(self.preview_frame, text=f"📂 {category}/", 
                        font=self.medium_font, text_color=self.primary_color).grid(row=row_idx, column=0, padx=15, pady=2, sticky="w")
            row_idx += 1

            if files_in_category:
                for file_name in files_in_category:
                    file_display_text = f"    📄 {file_name}"
                    if "(Não processável)" in file_name:
                        file_display_text = f"    🚫 {file_name}"
                        ctk.CTkLabel(self.preview_frame, text=file_display_text, 
                                    font=self.small_font, text_color="orange").grid(row=row_idx, column=0, padx=15, pady=1, sticky="w")
                    else:
                        ctk.CTkLabel(self.preview_frame, text=file_display_text, 
                                    font=self.small_font, text_color=self.text_color).grid(row=row_idx, column=0, padx=15, pady=1, sticky="w")
                    row_idx += 1
            else:
                ctk.CTkLabel(self.preview_frame, text="    (Nenhum arquivo para esta categoria)", 
                            font=self.small_italic_font, text_color="gray").grid(row=row_idx, column=0, padx=15, pady=1, sticky="w")
                row_idx += 1
        
        ctk.CTkLabel(self.preview_frame, text="\nDetalhes de Classificação por Arquivo:", 
                    font=self.medium_font, text_color=self.text_color).grid(row=row_idx, column=0, padx=5, pady=10, sticky="w")
        row_idx += 1

        if self.files_info:
            for file_name, category, date_str in self.files_info:
                detail_text = f"Arquivo: {file_name}\n  -> Categoria Sugerida: {category}"
                if date_str != "Nenhuma":
                    detail_text += f"\n  -> Datas Encontradas: {date_str}"
                
                detail_color = self.text_color
                if "(Não processável)" in category:
                    detail_color = "orange"
                    detail_text = f"Arquivo: {file_name}\n  -> NÃO PROCESSADO (Formato não suportado/Erro)"


                ctk.CTkLabel(self.preview_frame, text=detail_text, justify="left", 
                            font=self.small_font, text_color=detail_color).grid(row=row_idx, column=0, padx=15, pady=5, sticky="w")
                row_idx += 1
        else:
            ctk.CTkLabel(self.preview_frame, text="Nenhum arquivo processável encontrado.", 
                        font=self.small_italic_font, text_color="gray").grid(row=row_idx, column=0, padx=15, pady=5, sticky="w")


    def _confirm_organization(self):
        self.confirmed = True
        self.destroy()

    def _cancel_organization(self):
        self.confirmed = False
        self.destroy()

# --- Inicializador do Aplicativo ---
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()