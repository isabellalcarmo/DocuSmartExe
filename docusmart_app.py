import customtkinter as ctk
import os
import shutil
import CTkMessagebox
import organizer 
import threading
import sys
import config
import webbrowser
import re
import threading
import json


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        window_width = 900
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.withdraw() 

        self.title("DocuSmart - Organizador de Documentos")

        self.big_font = ctk.CTkFont(family="Arial", size=18, weight="bold")
        self.medium_font = ctk.CTkFont(family="Arial", size=16)
        self.small_font = ctk.CTkFont(family="Arial", size=14)

        self.primary_color = "#3498db"  
        self.secondary_color = "#2ecc71" 
        self.signup_color = "#f39c12"   
        self.gemini_button_color = "#9b59b6" 
        self.gemini_button_hover_color = "#8e44ad"
        self.cancel_color = "#e74c3c"   
        self.text_color = "#2c3e50"     
        self.bg_color = "#ecf0f1"       
        self.frame_color = "#ffffff"    
        self.disabled_entry_bg_color = "#e8e8e8" 
        self.log_bg_color = "#f8f8f8"   
        self.log_text_color = "#333333" 

        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 

        self.default_categories = {
            "Pessoal": "Documentos de identificação e registro civil, como RG (Registro Geral), CPF (Cadastro de Pessoa Física), CNH (Carteira Nacional de Habilitação), certidão de nascimento, certidão de casamento, passaporte, título de eleitor. Esta é uma descrição um pouco mais longa para testar a funcionalidade de scroll na caixa de texto e ver como ela se comporta com conteúdo que excede a altura inicial visível.",
            "Saúde": "Registros e informações médicas, como resultados de exames laboratoriais (sangue, urina, imagem como raio-x, ultrassom, ressonância), laudos médicos, receitas de medicamentos, atestados médicos, relatórios de consultas, histórico de vacinação, comprovantes de planos de saúde ou despesas médicas, relatórios médicos. Testando com mais texto para ver o scroll.",
            "Financeiro": "Comprovantes e extratos relacionados a transações monetárias e obrigações financeiras. Exemplos incluem boletos bancários, contas de consumo (água, luz, gás, telefone, internet), faturas de cartão de crédito, extratos bancários, comprovantes de pagamento, holerites (contracheques), declarações de imposto de renda, comprovantes de investimentos, nota fiscal.",
            "Jurídico": "Documentos legais, como procurações, contratos sociais, petições, contratos de trabalho, termos de serviço, acordos, notificações judiciais.",
            "Imagens": "Fotos, gráficos, capturas de tela, digitalizações de documentos, ilustrações. Esta categoria é para arquivos de imagem primariamente, e sua descrição pode ser concisa.",
            "Outros": "Documentos que não se encaixam claramente nas categorias anteriores ou que possuem um propósito muito diverso. Inclui arquivos temporários, downloads variados, documentos sem identificação clara de tema, ou itens que aguardam uma classificação manual."
        }
        self.current_categories = self.default_categories.copy()

        self.control_frame = ctk.CTkFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.control_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        self.control_frame.grid_columnconfigure(0, weight=1) 

        ctk.CTkLabel(self.control_frame, text="Passo 1: Selecione a pasta com seus documentos", font=self.big_font, text_color=self.text_color).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        self.select_folder_button = ctk.CTkButton(self.control_frame, text="📂 Selecionar Pasta", command=self.select_folder, font=self.medium_font, fg_color=self.primary_color, hover_color="#2980b9", state="disabled")
        self.select_folder_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.selected_folder_path = ctk.CTkLabel(self.control_frame, text="Nenhuma pasta selecionada.", font=self.small_font, text_color=self.text_color, wraplength=700)
        self.selected_folder_path.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(self.control_frame, text="Passo 2: Verifique e gerencie suas categorias", font=self.big_font, text_color=self.text_color).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        self.manage_categories_button = ctk.CTkButton(self.control_frame, text="⚙️ Gerenciar Categorias", command=self.open_category_manager, font=self.medium_font, fg_color=self.primary_color, hover_color="#2980b9", state="disabled")
        self.manage_categories_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.control_frame, text="Passo 3: Visualize a Organização", font=self.big_font, text_color=self.text_color).grid(row=5, column=0, columnspan=2, padx=10, pady=(20,5), sticky="w")
        
        preview_buttons_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        preview_buttons_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        preview_buttons_frame.grid_columnconfigure(0, weight=1)
        preview_buttons_frame.grid_columnconfigure(1, weight=1)

        self.preview_with_local_button = ctk.CTkButton(preview_buttons_frame, text="🔍 Visualizar (Modelo Local)", command=lambda: self.show_organization_preview(use_gemini_for_this_run=False), state="disabled", font=self.medium_font, fg_color=self.secondary_color, hover_color="#27ae60")
        self.preview_with_local_button.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")

        self.preview_with_gemini_button = ctk.CTkButton(preview_buttons_frame, text="✨ Visualizar (IA Gemini)", command=lambda: self.show_organization_preview(use_gemini_for_this_run=True), state="disabled", font=self.medium_font, fg_color=self.gemini_button_color, hover_color=self.gemini_button_hover_color)
        self.preview_with_gemini_button.grid(row=0, column=1, padx=(5,0), pady=5, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.control_frame, orientation="horizontal", mode="determinate", height=20, corner_radius=5, fg_color="#ecf0f1", progress_color="#2f714b")
        self.progress_bar.grid(row=7, column=0, padx=10, pady=10, sticky="ew") 
        self.progress_bar.set(0); self.progress_bar.grid_remove()

        self.progress_label = ctk.CTkLabel(self.control_frame, text="Aguardando...", font=self.small_font, text_color=self.text_color)
        self.progress_label.grid(row=8, column=0, padx=10, pady=2, sticky="w") 
        self.progress_label.grid_remove()

        self.log_textbox = ctk.CTkTextbox(self, width=600, height=300, font=self.small_font, text_color=self.log_text_color, fg_color=self.log_bg_color)
        self.log_textbox.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        self.log_textbox.insert("end", "Bem-vindo ao DocuSmart!\nFaça login para começar.\n")
        self.log_textbox.configure(state="disabled")

        self.user_session = None
        self.current_user = None 
        self.user_credits_remaining = 0
        self.user_credits_total = 0

        self.after(50, self.show_login_window)

    def show_login_window(self):
        login_win = LoginWindow(self)
        login_win.grab_set() 

    def show_main_application_ui(self):
        self.deiconify(); self.lift(); self.focus_force()
        self.select_folder_button.configure(state="normal")
        self.manage_categories_button.configure(state="normal")
        self.log_message(f"Usuário {self.current_user.email} logado. Sistema pronto para uso.")
        if self.user_credits_remaining > 0:
            self.log_message(f"Você possui {self.user_credits_remaining} créditos para usar com a IA Gemini.")
        else:
            self.log_message("Créditos para IA Gemini esgotados ou não disponíveis.")
        self._update_preview_button_states()
        self.update_idletasks()

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n\n") 
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def update_progress(self, current_val, total_val): 
        self.after(10, lambda: self._update_progress_ui(current_val, total_val))

    def _update_progress_ui(self, current_val, total_val):
        if total_val > 0:
            progress_value = current_val / total_val
            self.progress_bar.set(progress_value)
            self.progress_label.configure(text=f"Processando {current_val}/{total_val} arquivos...")
            self.update_idletasks()

    def select_folder(self):
        folder_selected = ctk.filedialog.askdirectory()
        if folder_selected:
            self.selected_folder_path.configure(text=f"Pasta selecionada: {folder_selected}")
            self.folder_to_organize = folder_selected
            self.log_message(f"Pasta '{folder_selected}' selecionada com sucesso.")
        else:
            self.selected_folder_path.configure(text="Nenhuma pasta selecionada.")
            self.folder_to_organize = None 
            self.log_message("Seleção de pasta cancelada.")
        self._update_preview_button_states() 
        self.progress_bar.grid_remove(); self.progress_label.grid_remove()
        self.progress_bar.set(0); self.progress_label.configure(text="Aguardando...")

    def show_organization_preview(self, use_gemini_for_this_run: bool):
        if not hasattr(self, 'folder_to_organize') or not self.folder_to_organize:
            CTkMessagebox.CTkMessagebox(title="Pasta não Selecionada", message="Por favor, selecione uma pasta primeiro.", icon="warning", master=self)
            return
        if not self.current_categories or len(self.current_categories) == 0:
            CTkMessagebox.CTkMessagebox(title="Sem Categorias", message="Por favor, defina suas categorias.", icon="warning", master=self)
            return

        effective_use_gemini = False 

        if use_gemini_for_this_run:
            if self.user_credits_remaining <= 0 : 
                CTkMessagebox.CTkMessagebox(master=self, title="Créditos Insuficientes", 
                                            message=f"Você não possui créditos para usar a IA Gemini (Restantes: {self.user_credits_remaining}).\nO modelo local será usado.", 
                                            icon="warning")
                self.log_message("Tentativa de usar IA Gemini sem créditos. Usando modelo local.")
            else:
                try:
                    num_files = len([f for f in os.listdir(self.folder_to_organize) if os.path.isfile(os.path.join(self.folder_to_organize, f))])
                except Exception as e:
                    self.log_message(f"Erro ao contar arquivos na pasta: {e}")
                    CTkMessagebox.CTkMessagebox(master=self, title="Erro", message=f"Não foi possível ler os arquivos da pasta selecionada.\n{e}", icon="cancel")
                    self._update_preview_button_states()
                    return

                msg_text = (f"Você selecionou {num_files} arquivo(s) e possui {self.user_credits_remaining} crédito(s) para a IA Gemini.\n"
                            f"Cada arquivo processado pela IA Gemini consumirá 1 crédito.\n\n")
                
                if num_files > self.user_credits_remaining:
                    msg_text += (f"A IA Gemini classificará os primeiros {self.user_credits_remaining} arquivo(s).\n"
                                f"Os {num_files - self.user_credits_remaining} arquivo(s) restante(s) serão classificados pelo modelo local.\n\n")
                msg_text += "Deseja continuar?"

                msg = CTkMessagebox.CTkMessagebox(master=self, title="Confirmar Uso de Créditos", message=msg_text, icon="question", option_1="Cancelar", option_2="Sim, Continuar")

                response = msg.get()
                if response == "Sim, Continuar":
                    effective_use_gemini = True
                    self.log_message("Modo IA Gemini ATIVADO para esta simulação (custará créditos).")
                else:
                    self.log_message("Visualização com IA Gemini cancelada pelo usuário.")
                    self._update_preview_button_states() 
                    return 
        else:
            self.log_message("Modo Local selecionado para esta simulação.")

        self.preview_with_local_button.configure(state="disabled"); self.preview_with_gemini_button.configure(state="disabled")
        self.select_folder_button.configure(state="disabled"); self.manage_categories_button.configure(state="disabled")
        self.progress_bar.grid(); self.progress_label.grid()
        self.progress_bar.set(0); self.progress_label.configure(text="Iniciando processamento de arquivos...")
        self.update_idletasks(); self.log_message("Simulando organização para prévia...")

        self.simulation_thread = threading.Thread(
            target=self._run_simulation_in_thread, 
            args=(effective_use_gemini, self.user_credits_remaining if effective_use_gemini else 0),
            daemon=True
        )
        self.simulation_thread.start()

    def _run_simulation_in_thread(self, use_gemini_decision, available_credits_to_gemini): 
        files_info, structure_info, gemini_calls_count = organizer.simulate_organization(
            folder_path=self.folder_to_organize, 
            categories_dict=self.current_categories, 
            progress_callback=self.update_progress,
            use_gemini=use_gemini_decision,
            available_credits_for_simulation=available_credits_to_gemini
        )
        self.after(0, lambda: self._post_simulation_ui_update(files_info, structure_info, gemini_calls_count))

    def _post_simulation_ui_update(self, files_info, structure_info, gemini_calls_count): 
        self.progress_bar.grid_remove(); self.progress_label.grid_remove()
        self.progress_bar.set(0); self.progress_label.configure(text="Aguardando...")

        if gemini_calls_count > 0:
            self.log_message(f"Processando dedução de {gemini_calls_count} créditos pela visualização com IA Gemini...")
            self.update_user_credits(gemini_calls_count) 

        self._update_preview_button_states() 

        if not files_info and not structure_info:
            self.log_message("Nenhum arquivo processável encontrado na pasta.")
            return

        preview_window = OrganizationPreview(self, files_info, structure_info, list(self.current_categories.keys()))
        preview_window.grab_set()

    def _update_preview_button_states(self):
        if self.user_session:
            folder_is_selected = hasattr(self, 'folder_to_organize') and self.folder_to_organize
            self.select_folder_button.configure(state="normal")
            self.manage_categories_button.configure(state="normal")
            if folder_is_selected:
                self.preview_with_local_button.configure(state="normal")
                if self.user_credits_remaining > 0: 
                    self.preview_with_gemini_button.configure(state="normal")
                else:
                    self.preview_with_gemini_button.configure(state="disabled")
            else:
                self.preview_with_local_button.configure(state="disabled")
                self.preview_with_gemini_button.configure(state="disabled")
        else: 
            self.select_folder_button.configure(state="disabled"); self.manage_categories_button.configure(state="disabled")
            self.preview_with_local_button.configure(state="disabled"); self.preview_with_gemini_button.configure(state="disabled")

    def handle_preview_confirmation(self, confirmed, final_files_info):
        if confirmed:
            self.log_message("Prévia confirmada. Iniciando organização real...")
            self.preview_with_local_button.configure(state="disabled"); self.preview_with_gemini_button.configure(state="disabled")
            self.select_folder_button.configure(state="disabled"); self.manage_categories_button.configure(state="disabled")
            thread_exec = threading.Thread(target=self._execute_organization_real, args=(final_files_info,), daemon=True)
            thread_exec.start()
        else:
            self.log_message("Organização cancelada pelo usuário ou janela fechada.")
        self._update_preview_button_states() 

    def _execute_organization_real(self, files_info):
        self.log_message("Iniciando a movimentação dos arquivos...")
        self.after(0, lambda: self.progress_bar.grid()); self.after(0, lambda: self.progress_label.grid())
        self.after(0, lambda: self.progress_bar.set(0)); self.after(0, lambda: self.progress_label.configure(text="Movendo arquivos..."))
        total_files_to_move = len(files_info)
        if total_files_to_move == 0:
            self.after(0, lambda: self.log_message("Nenhum arquivo para mover."))
            self.after(0, lambda: self.progress_bar.grid_remove()); self.after(0, lambda: self.progress_label.grid_remove())
            self.after(0, self._update_preview_button_states); return
        for i, file_data_tuple in enumerate(files_info):
            filename, classified_category, _, _ = file_data_tuple 
            original_file_path = os.path.join(self.folder_to_organize, filename)
            if classified_category == "Outros (Não processável)": 
                self.after(0, lambda f=filename: self.log_message(f"Pulando '{f}' (Não processável)."))
                self.update_progress(i + 1, total_files_to_move); continue 
            target_category_path = os.path.join(self.folder_to_organize, classified_category)
            if not os.path.exists(target_category_path):
                try: os.makedirs(target_category_path); self.after(0, lambda tc=target_category_path: self.log_message(f"Criando pasta: '{tc}'")) 
                except OSError as e: self.after(0, lambda tc=target_category_path, err=str(e): self.log_message(f"Erro ao criar pasta '{tc}': {err}")); self.update_progress(i + 1, total_files_to_move); continue
            try:
                target_file_path = os.path.join(target_category_path, filename)
                if os.path.exists(target_file_path):
                    base, ext = os.path.splitext(filename); count = 1; new_filename = filename
                    while os.path.exists(target_file_path): new_filename = f"{base}_{count}{ext}"; target_file_path = os.path.join(target_category_path, new_filename); count += 1
                    self.after(0, lambda fn=filename, nfn=os.path.basename(target_file_path) : self.log_message(f"Arquivo '{fn}' já existe. Renomeando para '{nfn}'."))
                shutil.move(original_file_path, target_file_path)
                self.after(0, lambda fn=os.path.basename(original_file_path), cc=classified_category: self.log_message(f"Arquivo '{fn}' movido para '{cc}'."))
            except Exception as e: self.after(0, lambda fn=filename, err=str(e): self.log_message(f"Erro ao mover '{fn}': {err}"))
            self.update_progress(i + 1, total_files_to_move)
        self.after(0, lambda: self.log_message("Organização finalizada com sucesso!"))
        self.after(0, lambda: self.progress_bar.grid_remove()); self.after(0, lambda: self.progress_label.grid_remove())
        self.after(0, lambda: self.progress_bar.set(0)); self.after(0, lambda: self.progress_label.configure(text="Aguardando..."))
        self.after(0, self._update_preview_button_states) 

    def update_user_credits(self, credits_used=1):
        if not config.supabase or not self.current_user or not self.user_session: self.log_message("Erro: Usuário não logado."); return False
        try:
            current_db_credits_resp = config.supabase.table("profiles").select("credits_remaining").eq("id", self.current_user.id).single().execute()
            if not current_db_credits_resp.data: self.log_message("Não foi possível buscar créditos atuais."); return False
            current_db_credits = current_db_credits_resp.data.get("credits_remaining", 0)
            new_credits_to_set = max(0, current_db_credits - credits_used)
            response = config.supabase.table("profiles").update({"credits_remaining": new_credits_to_set}).eq("id", self.current_user.id).execute()
            if response.data:
                self.user_credits_remaining = new_credits_to_set 
                self.log_message(f"Créditos atualizados. Restantes: {self.user_credits_remaining}")
                return True
            else:
                error_message = "Erro desconhecido ao atualizar créditos."
                if hasattr(response, 'error') and response.error: error_message = response.error.message
                self.log_message(f"Falha ao atualizar créditos: {error_message}"); return False
        except Exception as e: self.log_message(f"Erro ao atualizar créditos: {e}"); return False

    def open_category_manager(self):
        self.select_folder_button.configure(state="disabled"); self.manage_categories_button.configure(state="disabled")
        self.preview_with_local_button.configure(state="disabled"); self.preview_with_gemini_button.configure(state="disabled")
        category_manager_window = CategoryManager(self); category_manager_window.grab_set()
    
    def handle_category_manager_close(self, updated_categories):
        if updated_categories is not None: self.current_categories = updated_categories; self.log_message("Categorias atualizadas.")
        else: self.log_message("Gerenciamento de categorias cancelado.")
        self._update_preview_button_states()


class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.title("Acesso DocuSmart")

        window_width, window_height = 450, 560
        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((self.winfo_screenheight() / 2) - (window_height / 2))

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close_login_window)

        self.big_font_login = ctk.CTkFont(family="Arial", size=22, weight="bold")
        self.medium_font_login = ctk.CTkFont(family="Arial", size=16)
        self.small_italic_font = ctk.CTkFont(family="Arial", size=13, slant="italic")

        self.email_entry = None
        self.password_entry = None
        self.full_name_entry = None
        self.status_label = None

        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(pady=20, padx=50, fill="both", expand=True)

        self._create_initial_view()

    def _clear_frame(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

    def _create_initial_view(self):
        self._clear_frame()
        self.title("Acesso DocuSmart")

        ctk.CTkLabel(self.form_frame, text="Bem-vindo ao DocuSmart!", font=self.big_font_login, text_color=self.master.primary_color).pack(pady=(25, 10))
        
        ctk.CTkLabel(self.form_frame, 
                    text="Organização inteligente ao seu alcance.",
                    font=self.small_italic_font,
                    wraplength=380,
                    justify="center").pack(pady=(0, 30))

        login_btn = ctk.CTkButton(self.form_frame, text="Fazer Login", command=self._create_login_view, font=self.medium_font_login, fg_color=self.master.primary_color, hover_color="#2980b9")
        login_btn.pack(pady=10, fill="x", ipady=4)

        signup_btn = ctk.CTkButton(self.form_frame, text="Criar Conta", command=self._create_signup_view, font=self.medium_font_login, fg_color=self.master.signup_color, hover_color="#e67e22")
        signup_btn.pack(pady=10, fill="x", ipady=4)

        self.status_label = ctk.CTkLabel(self.form_frame, text="", wraplength=380, font=self.master.small_font)
        self.status_label.pack(pady=(20, 10))

    def _create_login_view(self):
        self._clear_frame()
        self.title("Login")

        ctk.CTkLabel(self.form_frame, text="Email:", font=self.medium_font_login).pack(anchor="w", pady=(10, 2))
        self.email_entry = ctk.CTkEntry(self.form_frame, width=300, font=self.medium_font_login)
        self.email_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.form_frame, text="Senha:", font=self.medium_font_login).pack(anchor="w", pady=(5, 2))
        self.password_entry = ctk.CTkEntry(self.form_frame, show="*", width=300, font=self.medium_font_login)
        self.password_entry.pack(fill="x", pady=(0, 20))

        enter_button = ctk.CTkButton(self.form_frame, text="Entrar", command=self._attempt_login, font=self.medium_font_login, fg_color=self.master.primary_color, hover_color="#2980b9")
        enter_button.pack(fill="x", pady=(5, 10), ipady=4)

        forgot_password_button = ctk.CTkButton(self.form_frame, text="Esqueceu sua senha?", command=self._open_password_reset_link, font=self.master.small_font, text_color=self.master.primary_color, fg_color="transparent")
        forgot_password_button.pack(pady=(0, 10))

        back_button = ctk.CTkButton(self.form_frame, text="Voltar", command=lambda: self.after(0, self._create_initial_view), font=self.medium_font_login, fg_color="gray60", hover_color="gray50")
        back_button.pack(fill="x", pady=(10, 0))

        self.status_label = ctk.CTkLabel(self.form_frame, text="", wraplength=380, font=self.master.small_font)
        self.status_label.pack(pady=(15, 10))

    def _create_signup_view(self):
        self._clear_frame()
        self.title("Criar Nova Conta")

        ctk.CTkLabel(self.form_frame, text="Nome Completo:", font=self.medium_font_login).pack(anchor="w", pady=(10, 2))
        self.full_name_entry = ctk.CTkEntry(self.form_frame, width=300, font=self.medium_font_login)
        self.full_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.form_frame, text="Email:", font=self.medium_font_login).pack(anchor="w", pady=(5, 2))
        self.email_entry = ctk.CTkEntry(self.form_frame, width=300, font=self.medium_font_login)
        self.email_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.form_frame, text="Senha (mín. 6 caracteres):", font=self.medium_font_login).pack(anchor="w", pady=(5, 2))
        self.password_entry = ctk.CTkEntry(self.form_frame, show="*", width=300, font=self.medium_font_login)
        self.password_entry.pack(fill="x", pady=(0, 20))

        register_button = ctk.CTkButton(self.form_frame, text="Cadastrar", command=self._attempt_signup, font=self.medium_font_login, fg_color=self.master.signup_color, hover_color="#e67e22")
        register_button.pack(fill="x", pady=(5, 10), ipady=4)

        back_button = ctk.CTkButton(self.form_frame, text="Voltar", command=lambda: self.after(0, self._create_initial_view), font=self.medium_font_login, fg_color="gray60", hover_color="gray50")
        back_button.pack(fill="x", pady=(10, 0))

        self.status_label = ctk.CTkLabel(self.form_frame, text="", wraplength=380, font=self.master.small_font)
        self.status_label.pack(pady=(15, 10))

    def _is_valid_email(self, email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None

    def _on_close_login_window(self):
        if self.master.winfo_exists() and not self.master.user_session:
            self.master.log_message("Login não concluído. Encerrando.")
            self.master.destroy()
        else:
            if self.winfo_exists():
                self.destroy()

    def _attempt_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            self.status_label.configure(text="Email e senha são obrigatórios.")
            return
        if not self._is_valid_email(email):
            self.status_label.configure(text="Por favor, insira um endereço de e-mail válido.")
            return
        if not config.check_internet_connection():
            self.status_label.configure(text="Erro: Sem conexão com a internet.")
            CTkMessagebox.CTkMessagebox(master=self, title="Erro de Conexão", message="Verifique sua conexão com a internet.", icon="cancel")
            return
        if not config.supabase:
            self.status_label.configure(text="Erro: Falha na conexão com o serviço.")
            CTkMessagebox.CTkMessagebox(master=self, title="Erro de Serviço", message="Não foi possível conectar aos serviços online.", icon="cancel")
            return
        try:
            self.status_label.configure(text="Efetuando login..."); self.update_idletasks()
            session_response = config.supabase.auth.sign_in_with_password({"email": email, "password": password})
            self.master.user_session = session_response.session
            self.master.current_user = session_response.user
            profile_response = config.supabase.table("profiles").select("credits_remaining,credits_total,is_approved").eq("id",self.master.current_user.id).limit(1).single().execute()
            if profile_response.data:
                is_approved = profile_response.data.get("is_approved", False)
                if not is_approved:
                    self.status_label.configure(text="Sua conta ainda está aguardando aprovação.")
                    self.master.log_message(f"Tentativa de login de {email}: Conta aguardando aprovação.")
                    self.master.user_session = None
                    self.master.current_user = None
                    return
                self.master.user_credits_remaining = profile_response.data.get("credits_remaining", 0)
                self.master.user_credits_total = profile_response.data.get("credits_total", 0)
                self.status_label.configure(text="Login bem-sucedido!")
                self.update_idletasks()
                self.master.show_main_application_ui()
                self.destroy()
            else:
                self.status_label.configure(text="Perfil de usuário não encontrado.")
                self.master.log_message(f"Tentativa de login de {email}, mas o perfil não foi encontrado no banco de dados.")
                self.master.user_session = None
                self.master.current_user = None
                return
        except Exception as e:
            error_msg = str(e).splitlines()[0] if str(e).splitlines() else "Erro desconhecido"
            if "invalid login credentials" in error_msg.lower():
                error_msg = "Email ou senha inválidos."
            elif "email not confirmed" in error_msg.lower():
                error_msg = "Email ainda não confirmado. Verifique sua caixa de entrada."
            self.status_label.configure(text=f"Erro de login: {error_msg}")
            print(f"Login error: {e}")
            self.master.user_session = None
            self.master.current_user = None

    def _attempt_signup(self):
        full_name = self.full_name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not full_name or not email or not password:
            self.status_label.configure(text="Nome, email e senha são obrigatórios.")
            return
        if not self._is_valid_email(email):
            self.status_label.configure(text="Por favor, insira um endereço de e-mail válido.")
            return
        if len(password) < 6:
            self.status_label.configure(text="A senha deve ter pelo menos 6 caracteres.")
            return
        if not config.check_internet_connection():
            self.status_label.configure(text="Erro: Sem conexão com a internet.")
            CTkMessagebox.CTkMessagebox(master=self, title="Erro de Conexão", message="Verifique sua conexão com a internet.", icon="cancel")
            return
        if not config.supabase:
            self.status_label.configure(text="Erro: Falha na conexão com o serviço.")
            CTkMessagebox.CTkMessagebox(master=self, title="Erro de Serviço", message="Não foi possível conectar aos serviços online.", icon="cancel")
            return

        try:
            self.status_label.configure(text="Criando sua conta..."); self.update_idletasks()
            
            auth_response = config.supabase.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })

            if auth_response.user:
                self.status_label.configure(text="Conta criada! Verifique seu email para confirmar.")
                CTkMessagebox.CTkMessagebox(master=self, title="Conta Criada com Sucesso!", 
                                            message="Sua conta foi criada!\n\nEnviamos um link de confirmação para o seu e-mail. Por favor, clique no link para ativar sua conta e poder fazer o login.",
                                            icon="check")
                self.master.log_message(f"Nova conta registrada para {email}. Perfil será criado via gatilho.")

                self.after(50, self._create_initial_view)
            else:
                self.status_label.configure(text="Não foi possível registrar o usuário. Tente novamente.")

        except Exception as e:
            error_msg = str(e)
            if 'User already registered' in error_msg:
                error_msg = "Este email já está cadastrado."
            elif 'rate limit exceeded' in error_msg.lower():
                error_msg = "Muitas tentativas. Tente novamente mais tarde."
            elif 'weak password' in error_msg.lower():
                error_msg = "Senha muito fraca. Tente uma mais forte."
            else:
                error_msg = "Ocorreu um erro desconhecido."

            self.status_label.configure(text=f"Erro ao criar conta: {error_msg}")
            print(f"Signup error: {e}")

    def _open_password_reset_link(self):
        reset_link = "https://preview--smartdoc-organizer-ai.lovable.app/password-reset"
        try:
            webbrowser.open_new_tab(reset_link)
            self.master.log_message(f"Abrindo link de redefinição de senha: {reset_link}")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao abrir link: {e}")
            self.master.log_message(f"Erro ao abrir link de redefinição de senha: {e}")
            CTkMessagebox.CTkMessagebox(master=self,
                                        title="Erro",
                                        message=f"Não foi possível abrir o link de redefinição de senha.\nPor favor, acesse manualmente: {reset_link}",
                                        icon="cancel")


class CategoryManager(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("Gerenciar Categorias de Documentos")

        window_width, window_height = 800, 700

        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((self.winfo_screenheight() / 2) - (window_height / 2))

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.resizable(False, False)

        self.master = master
        self.current_categories = master.current_categories.copy()
        self.default_categories = master.default_categories 
        self.result_categories = None 
        self.big_font = master.big_font
        self.medium_font = master.medium_font
        self.small_font = master.small_font
        self.primary_color = master.primary_color
        self.secondary_color = master.secondary_color
        self.cancel_color = master.cancel_color
        self.text_color = master.text_color
        self.bg_color = master.bg_color
        self.frame_color = master.frame_color
        self.disabled_entry_bg_color = master.disabled_entry_bg_color
        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)

        ctk.CTkLabel(self, text="Defina ou Edite Suas Categorias de Documentos", font=self.big_font, text_color=self.text_color).grid(row=0, column=0, padx=20, pady=(20,10))

        self.category_list_frame = ctk.CTkScrollableFrame(self, label_text="Categorias Atuais e Descrições", height=350, fg_color=self.frame_color, corner_radius=10, label_font=self.medium_font)

        self.category_list_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.category_list_frame.grid_columnconfigure(0, weight=1)
        self.category_list_frame.grid_columnconfigure(1, weight=3)
        self.category_list_frame.grid_columnconfigure(2, weight=0)

        self.category_widgets = {}
        self.load_categories_to_display()

        self.add_category_frame = ctk.CTkFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.add_category_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.add_category_frame.grid_columnconfigure(1, weight=1) 

        ctk.CTkLabel(self.add_category_frame, text="✨ Adicionar Nova Categoria:", font=self.medium_font, text_color=self.text_color).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        
        ctk.CTkLabel(self.add_category_frame, text="Nome:", font=self.small_font, text_color=self.text_color).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.category_name_var = ctk.StringVar()
        self.category_name_var.trace_add("write", self._on_category_name_change)

        self.new_category_name_entry = ctk.CTkEntry(self.add_category_frame, placeholder_text="Ex: Pets", font=self.small_font, textvariable=self.category_name_var, fg_color=self.disabled_entry_bg_color, text_color=self.text_color)
        self.new_category_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        description_frame = ctk.CTkFrame(self.add_category_frame, fg_color="transparent")
        description_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        description_frame.grid_columnconfigure(1, weight=1)

        desc_label_frame = ctk.CTkFrame(description_frame, fg_color="transparent")
        desc_label_frame.grid(row=0, column=0, columnspan=3, sticky="ew")

        ctk.CTkLabel(desc_label_frame, text="Descrição:", font=self.small_font, text_color=self.text_color).pack(side="left")

        self.generate_desc_button = ctk.CTkButton(desc_label_frame, text="Sugerir Descrição com IA ✨", font=self.small_font, width=180, command=self._generate_description_ai_threaded)
        self.generate_desc_button.pack(side="right")

        ctk.CTkLabel(desc_label_frame, text="(Digite o nome primeiro)", font=ctk.CTkFont(family="Arial", size=11, slant="italic"), text_color="gray50").pack(side="right", padx=5)

        self.new_category_description_entry = ctk.CTkTextbox(description_frame, height=60, font=self.small_font, wrap="word", fg_color=self.disabled_entry_bg_color, text_color=self.text_color) 
        self.new_category_description_entry.grid(row=1, column=0, columnspan=3, pady=(5,0), sticky="ew")

        self.add_category_button = ctk.CTkButton(self.add_category_frame, text="➕ Adicionar Categoria", command=self.add_new_category, font=self.medium_font, fg_color=self.primary_color, hover_color="#2980b9")
        self.add_category_button.grid(row=3, column=0, columnspan=2, padx=10, pady=(15,10), sticky="ew")

        self.action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, padx=20, pady=(10,20), sticky="ew")
        self.action_buttons_frame.grid_columnconfigure((0,1,2), weight=1)

        self.reset_button = ctk.CTkButton(self.action_buttons_frame, text="🔄 Redefinir Padrão", command=self.reset_categories, font=self.medium_font, fg_color="gray60", hover_color="gray50")
        self.reset_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.save_button = ctk.CTkButton(self.action_buttons_frame, text="✅ Salvar e Fechar", command=self.save_and_close, font=self.medium_font, fg_color=self.secondary_color, hover_color="#27ae60")
        self.save_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.cancel_button = ctk.CTkButton(self.action_buttons_frame, text="❌ Cancelar", command=self._cancel_and_close, font=self.medium_font, fg_color=self.cancel_color, hover_color="#c0392b")
        self.cancel_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self._cancel_and_close)

    def _on_category_name_change(self, *args):
        self.generate_desc_button.configure(state="normal")

    def _generate_description_ai_threaded(self):
        category_name = self.new_category_name_entry.get().strip()
        if not category_name:
            CTkMessagebox.CTkMessagebox(master=self, title="Aviso", message="Por favor, digite um nome para a categoria primeiro.", icon="warning")
            return

        self.generate_desc_button.configure(state="disabled", text="Gerando...")
        self.new_category_description_entry.delete("0.0", "end")
        self.new_category_description_entry.insert("0.0", "Aguarde, a IA está pensando...")

        thread = threading.Thread(target=self._generate_description_ai, args=(category_name,))
        thread.daemon = True
        thread.start()

    def _generate_description_ai(self, category_name):
        is_success = False
        try:
            response_bytes = config.supabase.functions.invoke(
                "generate-category-description",
                invoke_options={'body': {'category_name': category_name}}
            )
            response_str = response_bytes.decode('utf-8')
            response_data = json.loads(response_str)

            description = ""
            if isinstance(response_data, dict) and response_data.get('description') and not response_data.get('error'):
                description = response_data['description']
                is_success = True
            else:
                error_detail = response_data.get('error', 'Resposta inesperada.')
                description = f"Erro: {error_detail}"
        except Exception as e:
            description = f"Erro de conexão: {e}"

        self.after(0, self._update_description_from_ai, description, is_success)
        
    def _update_description_from_ai(self, description, is_success):
        self.new_category_description_entry.delete("0.0", "end")
        self.new_category_description_entry.insert("0.0", description)

        if is_success:
            self.generate_desc_button.configure(state="disabled", text="Descrição Sugerida!")
        else:
            self.generate_desc_button.configure(state="normal", text="Sugerir Descrição com IA ✨")

    def load_categories_to_display(self):
        for widget in self.category_list_frame.winfo_children(): widget.destroy()
        self.category_widgets = {}; row_idx = 0

        for category_name, description in self.current_categories.items():
            name_label = ctk.CTkLabel(self.category_list_frame, text=category_name, font=self.medium_font, text_color=self.text_color)
            name_label.grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
            description_entry = ctk.CTkTextbox(self.category_list_frame, width=300, height=80, font=self.small_font, wrap="word", fg_color=self.frame_color, text_color="#6e7986")
            description_entry.insert("0.0", description)
            description_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")

            is_default_category = category_name in self.default_categories
            if is_default_category:
                description_entry.configure(state="disabled", fg_color=self.disabled_entry_bg_color) 
                if category_name.lower() in ["outros", "imagens"]:
                    ctk.CTkLabel(self.category_list_frame, text=" (Essencial)", font=self.small_font, text_color="gray").grid(row=row_idx, column=2, padx=5, pady=5, sticky="w")
                else:
                    remove_button = ctk.CTkButton(self.category_list_frame, text="Remover", command=lambda c=category_name: self.remove_category(c), width=80, fg_color=self.cancel_color, hover_color="#c0392b", font=self.small_font)
                    remove_button.grid(row=row_idx, column=2, padx=5, pady=5, sticky="e")
            else: 
                remove_button = ctk.CTkButton(self.category_list_frame, text="Remover", command=lambda c=category_name: self.remove_category(c), width=80, fg_color=self.cancel_color, hover_color="#c0392b", font=self.small_font)
                remove_button.grid(row=row_idx, column=2, padx=5, pady=5, sticky="e")
            self.category_widgets[category_name] = {"name_label": name_label, "description_entry": description_entry}
            row_idx += 1
        if not self.current_categories: ctk.CTkLabel(self.category_list_frame, text="Nenhuma categoria definida.", font=self.medium_font, text_color="gray").grid(row=0, column=0, columnspan=3, padx=5, pady=10)

    def add_new_category(self):
        name = self.new_category_name_entry.get().strip()
        if not name: 
            CTkMessagebox.CTkMessagebox(master=self, title="Aviso", message="O nome da categoria não pode estar vazio.", icon="warning")
            return

        normalized_name = name.capitalize()
        description = self.new_category_description_entry.get("0.0", "end-1c").strip()

        existing_categories_lower = [k.lower() for k in self.current_categories.keys()]
        if normalized_name.lower() in existing_categories_lower:
            CTkMessagebox.CTkMessagebox(master=self, title="Aviso", message=f"A categoria '{normalized_name}' já existe.", icon="warning")
            return

        if not description: 
            CTkMessagebox.CTkMessagebox(master=self, title="Aviso", message="A descrição da categoria não pode estar vazia.", icon="warning")
            return

        self.current_categories[normalized_name] = description
        self.new_category_name_entry.delete(0, "end")
        self.new_category_description_entry.delete("0.0", "end")
        self.master.log_message(f"Categoria '{normalized_name}' adicionada."); self.load_categories_to_display()

    def remove_category(self, category_name):
        if category_name.lower() in ["outros", "imagens"]:
            self.master.log_message("Não é possível remover categorias essenciais."); CTkMessagebox.CTkMessagebox(master=self, title="Aviso", message="Não é possível remover categorias essenciais ('Outros', 'Imagens').", icon="warning"); return
        response = CTkMessagebox.CTkMessagebox(master=self,title="Confirmar Exclusão",message=f"Tem certeza que deseja remover a categoria '{category_name}'?",icon="question",option_1="Não",option_2="Sim").get()
        if response == "Sim" and category_name in self.current_categories:
            del self.current_categories[category_name]
            self.master.log_message(f"Categoria '{category_name}' removida."); self.load_categories_to_display()

    def reset_categories(self):
        response = CTkMessagebox.CTkMessagebox(master=self,title="Confirmar Redefinição",message="Redefinir para categorias padrão?\nCategorias personalizadas serão perdidas.",icon="warning",option_1="Não",option_2="Sim").get()
        if response == "Sim":
            self.current_categories = self.master.default_categories.copy()
            self.master.log_message("Categorias redefinidas para o padrão."); self.load_categories_to_display()

    def save_and_close(self):
        temp_categories = {}
        valid_save = True
        for cat_name, widgets in self.category_widgets.items():
            normalized_cat_name = cat_name.capitalize()

            if normalized_cat_name in self.default_categories: 
                temp_categories[normalized_cat_name] = self.default_categories[normalized_cat_name]
            elif "description_entry" in widgets:
                desc = widgets["description_entry"].get("0.0", "end-1c").strip()
                if not desc: 
                    CTkMessagebox.CTkMessagebox(master=self, title="Descrição Vazia", message=f"A descrição da categoria personalizada '{normalized_cat_name}' não pode ser vazia.", icon="warning")
                    valid_save = False; break 
                temp_categories[normalized_cat_name] = desc

        if not valid_save: return

        for essential_cat in ["Outros", "Imagens"]:
            if essential_cat not in temp_categories:
                temp_categories[essential_cat] = self.master.default_categories.get(essential_cat, "")

        self.result_categories = temp_categories
        self.master.handle_category_manager_close(self.result_categories); self.destroy()

    def _cancel_and_close(self):
        self.master.handle_category_manager_close(None); self.destroy()


class OrganizationPreview(ctk.CTkToplevel):
    def __init__(self, master, files_info, structure_info, available_categories):
        super().__init__(master)

        self.title("Prévia da Organização")

        window_width, window_height = 1000, 750

        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((self.winfo_screenheight() / 2) - (window_height / 2))

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.resizable(False, False)
        self.master = master
        self.files_info = list(files_info)
        self.structure_info = structure_info
        self.available_categories = available_categories
        self.confirmed = False
        self.big_font=master.big_font
        self.medium_font=master.medium_font
        self.small_font=master.small_font
        self.primary_color=master.primary_color
        self.secondary_color=master.secondary_color
        self.cancel_color=master.cancel_color
        self.text_color=master.text_color
        self.bg_color=master.bg_color
        self.frame_color=master.frame_color

        self.small_italic_font = ctk.CTkFont(family="Arial", size=12, slant="italic")
        self.configure(fg_color=self.bg_color)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        ctk.CTkLabel(self, text="Verifique a prévia da organização antes de confirmar:", font=self.big_font, text_color=self.text_color).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.preview_frame = ctk.CTkScrollableFrame(self, fg_color=self.frame_color, corner_radius=10)
        self.preview_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1) 
        self._display_preview_content()
        self.action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_buttons_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.action_buttons_frame.grid_columnconfigure((0,1), weight=1)
        self.confirm_button = ctk.CTkButton(self.action_buttons_frame, text="✅ Confirmar Organização", command=self._confirm_organization, font=self.big_font, fg_color=self.secondary_color, hover_color="#27ae60")
        self.confirm_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cancel_button = ctk.CTkButton(self.action_buttons_frame, text="❌ Cancelar", command=self._cancel_organization, font=self.big_font, fg_color=self.cancel_color, hover_color="#c0392b")
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.protocol("WM_DELETE_WINDOW", self._cancel_organization)

    def _rebuild_structure_info(self):
        new_structure_info = {cat: [] for cat in self.master.current_categories.keys()}
        if any(fi[1] == "Outros (Não processável)" for fi in self.files_info) and "Outros (Não processável)" not in new_structure_info:
            new_structure_info["Outros (Não processável)"] = []
        for filename, category, _, _ in self.files_info: 
            if category not in new_structure_info: new_structure_info[category] = []
            new_structure_info[category].append(filename)
        self.structure_info = new_structure_info

    def _display_preview_content(self):
        for widget in self.preview_frame.winfo_children(): widget.destroy()
        row_idx = 0
        ctk.CTkLabel(self.preview_frame, text="Estrutura de Pastas e Conteúdo Estimado:", font=self.medium_font, text_color=self.text_color).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row_idx += 1; self._rebuild_structure_info()
        sorted_category_keys = list(self.master.current_categories.keys())
        if "Outros (Não processável)" in self.structure_info and "Outros (Não processável)" not in sorted_category_keys: sorted_category_keys.append("Outros (Não processável)")
        for category in sorted_category_keys:
            if category not in self.structure_info: continue 
            files_in_category = self.structure_info.get(category, [])
            ctk.CTkLabel(self.preview_frame, text=f"📂 {category}/", font=self.medium_font, text_color=self.primary_color).grid(row=row_idx, column=0, columnspan=2, padx=15, pady=(5,2), sticky="w")
            row_idx += 1
            if files_in_category:
                for file_name in files_in_category:
                    file_label_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
                    file_label_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=15) 
                    file_label_frame.grid_columnconfigure(0, weight=1); file_label_frame.grid_columnconfigure(1, weight=0) 
                    file_display_text = f"📄 {file_name}"; text_color_for_file = self.text_color
                    is_unprocessed = (category == "Outros (Não processável)")
                    if is_unprocessed: file_display_text = f"🚫 {file_name}"; text_color_for_file = "orange"
                    ctk.CTkLabel(file_label_frame, text=file_display_text, font=self.small_font, text_color=text_color_for_file).grid(row=0, column=0, pady=1, sticky="w")
                    if not is_unprocessed:
                        button_font = self.master.small_font; new_button_width = 100; new_button_height = 28 
                        modify_button = ctk.CTkButton(file_label_frame, text="Modificar", command=lambda fn=file_name, cat=category: self._open_modify_dialog(fn, cat), width=new_button_width, height=new_button_height, font=button_font, fg_color="gray60", hover_color="gray50")
                        modify_button.grid(row=0, column=1, padx=(0, 5), pady=1, sticky="e")
                    row_idx += 1
            else:
                ctk.CTkLabel(self.preview_frame, text="    (Nenhum arquivo para esta categoria)", font=self.small_italic_font, text_color="gray").grid(row=row_idx, column=0, columnspan=2, padx=30, pady=1, sticky="w")
                row_idx += 1
        ctk.CTkLabel(self.preview_frame, text="\nDetalhes de Classificação por Arquivo:", font=self.medium_font, text_color=self.text_color).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=10, sticky="w")
        row_idx += 1
        if self.files_info:
            for file_name, category, date_str, method in self.files_info:
                detail_text = f"Arquivo: {file_name}\n  -> Categoria: {category} (Método: {method})"
                if date_str != "Nenhuma" and date_str: detail_text += f"\n  -> Datas: {date_str}"
                detail_color = self.text_color
                if category == "Outros (Não processável)": detail_color = "orange"; detail_text = f"Arquivo: {file_name}\n  -> NÃO PROCESSADO"
                ctk.CTkLabel(self.preview_frame, text=detail_text, justify="left", font=self.small_font, text_color=detail_color, wraplength=self.preview_frame.winfo_width()-50).grid(row=row_idx, column=0, columnspan=2, padx=15, pady=5, sticky="w")
                row_idx += 1
        else: ctk.CTkLabel(self.preview_frame, text="Nenhum arquivo processável encontrado.", font=self.small_italic_font, text_color="gray").grid(row=row_idx, column=0, columnspan=2, padx=15, pady=5, sticky="w")

    def _open_modify_dialog(self, filename, current_category):
        valid_categories_for_selection = [cat for cat in self.master.current_categories.keys() if cat != "Outros (Não processável)"]
        modify_window = ModifyCategory(self, filename, current_category, valid_categories_for_selection)
        modify_window.grab_set()

    def handle_modify_category_close(self, original_filename, new_category):
        if new_category is not None: 
            for i, file_data in enumerate(self.files_info):
                fn, current_cat_before_modify, dates, original_method = file_data 
                if fn == original_filename:
                    method_to_set = "manual_override" if new_category != current_cat_before_modify else original_method
                    self.files_info[i] = (fn, new_category, dates, method_to_set) 
                    self.master.log_message(f"Categoria de '{fn}' alterada manualmente para '{new_category}'.")
                    break
            self._display_preview_content()

    def _confirm_organization(self):
        self.confirmed = True
        self.master.handle_preview_confirmation(self.confirmed, self.files_info)
        self.destroy()

    def _cancel_organization(self):
        self.confirmed = False
        self.master.handle_preview_confirmation(self.confirmed, self.files_info)
        self.destroy()


class ModifyCategory(ctk.CTkToplevel):
    def __init__(self, master_preview, filename, current_category, all_valid_categories): 
        super().__init__(master_preview) 

        self.title("Modificar Categoria"); window_width, window_height = 450, 280 

        center_x = int((self.winfo_screenwidth() / 2) - (window_width / 2))
        center_y = int((self.winfo_screenheight() / 2) - (window_height / 2))

        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.resizable(False, False)

        self.master_preview = master_preview
        self.original_filename = filename
        self.current_category_on_open = current_category
        self.new_category_selected = current_category 
        self.available_categories = sorted(all_valid_categories)

        app_master = master_preview.master 

        self.medium_font = app_master.medium_font
        self.small_font = app_master.small_font
        self.text_color = app_master.text_color
        self.bg_color = app_master.bg_color
        self.secondary_color = app_master.secondary_color
        self.cancel_color_app = app_master.cancel_color 

        self.configure(fg_color=self.bg_color)

        ctk.CTkLabel(self, text=f"Arquivo: {os.path.basename(filename)}", font=self.medium_font, text_color=self.text_color, wraplength=400).pack(padx=20, pady=(20,5), anchor="w")
        ctk.CTkLabel(self, text=f"Categoria Atual: {current_category}", font=self.small_font, text_color=self.text_color).pack(padx=20, pady=5, anchor="w")
        ctk.CTkLabel(self, text="Nova Categoria:", font=self.medium_font, text_color=self.text_color).pack(padx=20, pady=(10,2), anchor="w")

        self.category_optionmenu = ctk.CTkOptionMenu(self, values=self.available_categories, command=self._option_menu_callback, font=self.medium_font)
        
        if current_category in self.available_categories: 
            self.category_optionmenu.set(current_category)
        elif self.available_categories: 
            self.category_optionmenu.set(self.available_categories[0])
            self.new_category_selected = self.available_categories[0]
        else: 
            self.category_optionmenu.set("Nenhuma")
            self.category_optionmenu.configure(state="disabled")
            self.new_category_selected = None

        self.category_optionmenu.pack(padx=20, pady=(0,20), fill="x")

        action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_buttons_frame.pack(pady=10, fill="x", padx=20)
        action_buttons_frame.grid_columnconfigure((0,1), weight=1)

        confirm_button = ctk.CTkButton(action_buttons_frame, text="Confirmar", command=self._confirm_selection, font=self.medium_font, fg_color=self.secondary_color, hover_color="#27ae60") 
        confirm_button.grid(row=0, column=0, padx=5, sticky="ew")
        cancel_button = ctk.CTkButton(action_buttons_frame, text="Cancelar", command=self._cancel_and_close, font=self.medium_font, fg_color=self.cancel_color_app, hover_color="darkred")
        cancel_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self._cancel_and_close)

    def _option_menu_callback(self, choice):
        self.new_category_selected = choice

    def _confirm_selection(self):
        self.master_preview.handle_modify_category_close(self.original_filename, self.new_category_selected)
        self.destroy()

    def _cancel_and_close(self):
        self.master_preview.handle_modify_category_close(self.original_filename, None)
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    try:
        config.init_supabase()
    except Exception as e:
        print(f"Falha ao inicializar Supabase: {e}")
        root_err = ctk.CTk(); root_err.withdraw() 
        CTkMessagebox.CTkMessagebox(title="Erro Crítico de Conexão", 
                                    message=f"Não foi possível conectar aos serviços online: {e}\nO aplicativo será encerrado.", 
                                    icon="cancel")
        sys.exit(1)
    app = App()
    app.mainloop()