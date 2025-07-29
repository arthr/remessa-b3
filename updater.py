import sys
import os
import tkinter as tk
from pathlib import Path

# Adicionar o diretório src ao sys.path para permitir importações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.updater_window import UpdaterWindow
from src.services.update_service import UpdateService

def main():
    """Função principal do atualizador"""
    # Verificar argumentos
    if len(sys.argv) < 4:
        print("Uso: updater.py <download_url> <versao> <app_executable>")
        return
    
    # Extrair argumentos
    download_url = sys.argv[1]
    versao = sys.argv[2]
    app_exec = sys.argv[3]
    
    # Criar UpdateService
    update_service = UpdateService()
    
    # Iniciar interface
    root = tk.Tk()
    root.withdraw()  # Ocultar janela raiz
    
    # Criar UpdaterWindow com injeção de dependência
    updater_window = UpdaterWindow(root, download_url, versao, app_exec, update_service)
    updater_window.run()

if __name__ == "__main__":
    main()