# src/main.py
import sys
import os
import tkinter as tk
import threading
import time
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Usar imports absolutos
from src.config.settings import Settings
from src.config.constants import AppConstants
from src.database.connection import DatabaseConnection
from src.services.bordero_service import BorderoService
from src.services.file_service import FileService
from src.services.backup_service import BackupService
from src.services.update_service import UpdateService
from src.services.history_service import HistoryService
from src.ui.splash_screen import SplashScreen
from src.ui.main_window import MainWindow
from src.ui.ui_manager import UIManagerImpl
from src.ui.dialogs.update_available import UpdateAvailableDialog

def main():
    """Ponto de entrada principal da aplicação"""
    main_window = None
    splash = None
    root = None
    
    try:
        print("Iniciando aplicação...")
        
        # Criar janela raiz temporária para a splash screen
        root = tk.Tk()
        root.withdraw()  # Ocultar a janela raiz
        
        # Criar e mostrar splash screen
        splash = SplashScreen(root)
        
        # Atualizar progresso da splash screen
        splash.update_progress(10, "Carregando configurações...")
        
        # Carregar configurações
        settings = Settings()
        
        splash.update_progress(20, "Inicializando BorderoService...")
        
        # Inicializar serviços com progresso detalhado
        bordero_service = BorderoService()
        
        splash.update_progress(30, "Inicializando FileService...")
        file_service = FileService()
        
        splash.update_progress(40, "Inicializando BackupService...")
        backup_service = BackupService()
        
        splash.update_progress(50, "Inicializando HistoryService...")
        history_service = HistoryService()
        
        splash.update_progress(60, "Inicializando UpdateService...")
        update_service = UpdateService()
        
        splash.update_progress(70, "Verificando atualizações...")
        
        # Verificar atualizações em background
        update_info = update_service.check_for_updates()
        
        splash.update_progress(80, "Configurando gerenciador de UI...")
        
        # Inicializar UIManager
        ui_manager = UIManagerImpl(update_service)
        
        splash.update_progress(90, "Configurando interface principal...")
        
        # Inicializar janela principal
        main_window = MainWindow(
            bordero_service,
            file_service,
            backup_service,
            update_service,
            ui_manager
        )
        
        splash.update_progress(95, "Finalizando...")
        time.sleep(0.5)  # Pequena pausa para mostrar 95%
        
        # Fechar splash screen
        splash.destroy()
        
        # Mostrar a janela principal
        root.deiconify()
        
        # Verificar atualizações em segundo plano
        if update_info.disponivel:
            # Usar after para agendar na thread principal
            root.after(1000, lambda: UpdateAvailableDialog(root, update_service))
        
        # Iniciar aplicação
        main_window.run()
        
    except KeyboardInterrupt:
        print("Interrupção detectada, encerrando...")
    except Exception as e:
        print(f"Erro ao inicializar aplicação: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Garantir encerramento limpo
        print("Finalizando aplicação...")
        
        try:
            if splash:
                splash.destroy()
        except:
            pass
            
        try:
            if main_window:
                main_window.is_running = False
                main_window.cancel_all_events()
        except:
            pass
            
        try:
            if root:
                root.quit()
                root.destroy()
        except:
            pass
        
        # Forçar saída limpa
        try:
            os._exit(0)
        except:
            sys.exit(0)

if __name__ == "__main__":
    main()