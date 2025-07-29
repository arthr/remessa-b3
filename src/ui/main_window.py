# src/ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import threading
import os
from pathlib import Path
from datetime import datetime
import re
from ..services.bordero_service import BorderoService
from ..services.file_service import FileService
from ..services.backup_service import BackupService
from ..services.update_service import UpdateService
from ..ui.ui_manager import UIManagerImpl
from ..ui.dialogs.update_available import UpdateAvailableDialog
from ..utils import centralizar_janela

class MainWindow:
    def __init__(self, bordero_service: BorderoService, 
                 file_service: FileService, 
                 backup_service: BackupService,
                 update_service: UpdateService,
                 ui_manager: UIManagerImpl):
        self.bordero_service = bordero_service
        self.file_service = file_service
        self.backup_service = backup_service
        self.update_service = update_service
        self.ui_manager = ui_manager
        
        # Variáveis de controle
        self.arquivo_salvo = None
        self.dados_ultima_consulta = None
        self.status_label = None
        self.progress_bar = None
        self.historico_list = None
        self.entry_bordero = None
        self.combobox_carteira = None
        self.gerar_botao = None
        self.abrir_botao = None
        
        self.root = ThemedTk(theme="azure")
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface principal"""
        self.root.title("Remessas B3 - Registro de Títulos")
        self.root.geometry("800x600")
        
        # Configurar estilos
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#f0f0f0")
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Status.TLabel", font=("Segoe UI", 9), padding=5)
        style.configure("Custom.TButton", font=("Segoe UI", 9), padding=5)
        
        # Centralizar janela
        centralizar_janela(self.root, 800, 600)
        
        # Configurar menu
        self.setup_menu()
        
        # Configurar interface principal
        self.setup_main_frame()
        
        # Configurar barra de status
        self.setup_status_bar()
    
    def setup_menu(self):
        """Configura o menu da aplicação"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Menu Arquivo
        arquivo_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Arquivo", menu=arquivo_menu)
        arquivo_menu.add_command(label="Gerar Novo Arquivo", command=self.iniciar_geracao)
        arquivo_menu.add_command(label="Abrir Último Arquivo", command=self.file_service.abrir_arquivo)
        arquivo_menu.add_command(label="Abrir Arquivo de Backup", command=self.abrir_backup)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Ver Detalhes da Situação", 
                               command=lambda: self.mostrar_detalhes_situacao(self.dados_ultima_consulta) if self.dados_ultima_consulta else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."))
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Limpar Histórico e Backups", command=self.limpar_historico_e_backups)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Ajuda
        ajuda_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
        ajuda_menu.add_command(label="Verificar Atualizações", 
                             command=lambda: threading.Thread(target=lambda: UpdateAvailableDialog(self.root, self.update_service) if self.update_service.get_update_info().disponivel else messagebox.showinfo("Atualização", "Você já está usando a versão mais recente."), daemon=True).start())
        ajuda_menu.add_command(label="Ver Configurações", command=self.mostrar_configuracoes)
        ajuda_menu.add_command(label="Sobre", command=self.sobre)
    
    def setup_main_frame(self):
        """Configura o frame principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style="Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Área de entrada de dados
        input_frame = ttk.LabelFrame(main_frame, text="Dados de Entrada", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Grid para campos de entrada
        ttk.Label(input_frame, text="Número do Borderô:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_bordero = ttk.Entry(input_frame, width=30)
        self.entry_bordero.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_bordero.bind("<Return>", self.iniciar_geracao)
        
        ttk.Label(input_frame, text="Filtrar por Carteira:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combobox_carteira = ttk.Combobox(input_frame, values=["Todas", "Carteira FIDC", "Carteira Própria"], 
                                        state="readonly", width=27)
        self.combobox_carteira.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.combobox_carteira.set("Todas")
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.gerar_botao = ttk.Button(button_frame, text="Gerar Arquivo", command=self.iniciar_geracao, style="Custom.TButton")
        self.gerar_botao.pack(side=tk.LEFT, padx=5)
        
        self.abrir_botao = ttk.Button(button_frame, text="Abrir Arquivo", command=self.file_service.abrir_arquivo, 
                                state="disabled", style="Custom.TButton")
        self.abrir_botao.pack(side=tk.LEFT, padx=5)
        
        backup_botao = ttk.Button(button_frame, text="Abrir Backup", command=self.abrir_backup, style="Custom.TButton")
        backup_botao.pack(side=tk.LEFT, padx=5)
        
        detalhes_botao = ttk.Button(button_frame, text="Ver Detalhes", 
                                  command=lambda: self.mostrar_detalhes_situacao(self.dados_ultima_consulta) if self.dados_ultima_consulta else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."), 
                                  style="Custom.TButton")
        detalhes_botao.pack(side=tk.LEFT, padx=5)
        
        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=100)
        self.progress_bar.pack(fill=tk.X, padx=5)
        
        # Frame para histórico
        historico_frame = ttk.LabelFrame(main_frame, text="Histórico de Operações", padding=10)
        historico_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Lista de histórico com scrollbar
        historico_scroll = ttk.Scrollbar(historico_frame)
        historico_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.historico_list = tk.Listbox(historico_frame, yscrollcommand=historico_scroll.set, 
                                    font=("Segoe UI", 9), height=8)
        self.historico_list.pack(fill=tk.BOTH, expand=True)
        historico_scroll.config(command=self.historico_list.yview)
    
    def setup_status_bar(self):
        """Configura a barra de status"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Pronto para iniciar...", 
                                style="Status.TLabel", relief="sunken")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
    
    def iniciar_geracao(self, event=None):
        """Inicia a geração do arquivo"""
        # Implementação básica - será expandida conforme necessário
        self.atualizar_status("Funcionalidade de geração em desenvolvimento...", "info")
    
    def abrir_backup(self):
        """Abre a janela para selecionar e abrir um arquivo de backup"""
        # Implementação básica - será expandida conforme necessário
        self.atualizar_status("Funcionalidade de backup em desenvolvimento...", "info")
    
    def limpar_historico_e_backups(self):
        """Limpa o histórico de operações e os arquivos de backup"""
        # Implementação básica - será expandida conforme necessário
        self.atualizar_status("Funcionalidade de limpeza em desenvolvimento...", "info")
    
    def mostrar_detalhes_situacao(self, dados):
        """Mostra detalhes da situação"""
        # Implementação básica - será expandida conforme necessário
        self.atualizar_status("Funcionalidade de detalhes em desenvolvimento...", "info")
    
    def mostrar_configuracoes(self):
        """Mostra configurações"""
        # Implementação básica - será expandida conforme necessário
        self.atualizar_status("Funcionalidade de configurações em desenvolvimento...", "info")
    
    def sobre(self):
        """Mostra informações sobre a aplicação"""
        messagebox.showinfo("Sobre", "Remessa B3 - Sistema de Atualização\nVersão com arquitetura refatorada")
    
    def atualizar_status(self, mensagem, tipo="info"):
        """Atualiza a mensagem de status na barra inferior"""
        if not self.status_label:
            print(mensagem)
            return
            
        self.status_label.config(text=mensagem)
        if tipo == "error":
            self.status_label.config(foreground="red")
        elif tipo == "success":
            self.status_label.config(foreground="green")
        elif tipo == "warning":
            self.status_label.config(foreground="orange")
        else:
            self.status_label.config(foreground="black")
        self.root.update_idletasks()
    
    def run(self):
        """Executa a janela principal"""
        self.root.mainloop()