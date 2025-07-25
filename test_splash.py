#!/usr/bin/env python3
"""
Teste simples da SplashScreen
Execute este arquivo para testar se a SplashScreen está funcionando corretamente
"""

import sys
import tkinter as tk
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.splash_screen import SplashScreen

def test_splash_screen():
    """Testa a splash screen"""
    print("Iniciando teste da SplashScreen...")
    
    # Criar janela raiz
    root = tk.Tk()
    root.withdraw()  # Ocultar janela raiz
    
    try:
        # Criar splash screen
        splash = SplashScreen(root)
        
        # Simular progresso
        for i in range(0, 101, 10):
            splash.update_progress(i, f"Testando... {i}%")
            time.sleep(0.5)  # Pausa para visualizar
        
        print("SplashScreen funcionando corretamente!")
        
        # Fechar splash screen
        splash.destroy()
        
    except Exception as e:
        print(f"Erro no teste da SplashScreen: {e}")
    
    finally:
        root.destroy()

if __name__ == "__main__":
    test_splash_screen() 