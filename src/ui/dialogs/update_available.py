# src/ui/dialogs/update_available.py

import os
import sys
import tkinter as tk
from tkinter import ttk
import webbrowser
from ...config.settings import Settings
from ...services.update_service import UpdateService
from ...utils import centralizar_janela

class UpdateAvailableDialog:
    def __init__(self, parent, update_service: UpdateService):
        self.parent = parent
        self.root = tk.Toplevel(self.parent)
        self.settings = Settings()
        self.root.title(f"{self.settings.app_name} - Atualização Disponível")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        self.update_service = update_service
        self.update_info = self.update_service.get_update_info()
        self.setup_ui()
        
        # Centralizar janela
        centralizar_janela(self.root, 500, 450)

    def setup_ui(self):
        """Configura a interface da janela"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        ttk.Label(main_frame, text="Nova Versão Disponível!", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Informações da versão
        ttk.Label(main_frame, text=f"Versão atual: {self.settings.app_version}").pack(anchor="w", pady=2)
        ttk.Label(main_frame, text=f"Nova versão: {self.update_info['versao']}").pack(anchor="w", pady=2)

        # Notas de lançamento
        ttk.Label(main_frame, text="Notas de lançamento:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)

        # Frame para as notas com scrollbar
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(notes_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=10, yscrollcommand=scrollbar.set)
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)
        
        notes_text.insert(tk.END, self.update_info['notas'])
        notes_text.config(state=tk.DISABLED)
        
        # Botões
        self.setup_buttons()

    def setup_buttons(self):
        """Configura os botões da janela"""
        # Frame para os botões
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, pady=10, padx=5)

        # Botão de download
        ttk.Button(
            button_frame,
            text="Baixar e Instalar Automaticamente",
            command=lambda: self.update_service.run_updater(self.update_info['download_url'], self.update_info['versao'], os.path.abspath(sys.executable))
        ).pack(side=tk.LEFT, padx=5)

        # Botão de download manual
        ttk.Button(
            button_frame,
            text="Baixar Manualmente",
            command=lambda: self.open_download_page(self.update_info)
        ).pack(side=tk.LEFT, padx=5)

        # Botão de cancelar
        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self.root.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def open_download_page(self, update_info):
        """Abre a página de download no navegador"""
        webbrowser.open(update_info['url'])
        self.root.destroy()