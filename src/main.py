# src/main.py
import sys
import os
import tkinter as tk
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from config.constants import AppConstants
from database.connection import DatabaseConnection
from services.bordero_service import BorderoService
from services.file_service import FileService
from services.backup_service import BackupService
from services.update_service import UpdateService
from ui.splash_screen import SplashScreen
from ui.main_window import MainWindow
from ui.ui_manager import UIManagerImpl

def main():
    """Ponto de entrada principal da aplicação"""
    try:
        # Criar janela raiz temporária para a splash screen
        root = tk.Tk()
        root.withdraw()  # Ocultar a janela raiz
        
        # Criar e mostrar splash screen
        splash = SplashScreen(root)
        
        # Atualizar progresso da splash screen
        splash.update_progress(10, "Carregando configurações...")
        
        # Carregar configurações
        settings = Settings()
        
        splash.update_progress(20, "Inicializando serviços...")
        
        # Inicializar serviços
        db_connection = DatabaseConnection(settings)
        bordero_service = BorderoService(db_connection)
        file_service = FileService()
        backup_service = BackupService()
        update_service = UpdateService()
        
        splash.update_progress(40, "Configurando gerenciador de UI...")
        
        # Inicializar UIManager
        ui_manager = UIManagerImpl(update_service)
        
        splash.update_progress(50, "Configurando interface...")
        
        # Inicializar janela principal
        main_window = MainWindow(bordero_service, file_service, backup_service, update_service, ui_manager)
        
        splash.update_progress(90, "Finalizando...")
        
        # Fechar splash screen e mostrar janela principal
        splash.destroy()
        root.deiconify()  # Mostrar janela raiz se necessário
        
        # Iniciar aplicação
        main_window.run()
        
    except Exception as e:
        print(f"Erro ao inicializar aplicação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()