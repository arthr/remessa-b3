# src/updater/main.py
import sys
import os
import tkinter as tk
from pathlib import Path

# Adicionar o diretório src ao path para permitir importações
sys.path.insert(0, str(Path(__file__).parent.parent))

from updater_window import UpdaterWindow

def main(self):
    """Ponto de entrada do atualizador"""
    try:
        # Verificar argumentos
        if len(sys.argv) < 4:
            print("Uso: updater.py <download_url> <versao> <app_executable>")
            return
        
        # Extrair argumentos
        download_url = sys.argv[1]
        versao = sys.argv[2]
        app_exec = sys.argv[3]
        
        updater_window = UpdaterWindow(self, download_url, versao, app_exec)
        updater_window.run()
        
    except Exception as e:
        print(f"Erro no updater: {e}")
    finally:
        # Garantir saída limpa
        try:
            import os
            os._exit(0)
        except:
            pass

if __name__ == "__main__":
    main() 