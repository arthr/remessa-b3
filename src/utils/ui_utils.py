# src/utils/ui_utils.py
import tkinter as tk
from typing import Union

def centralizar_janela(root: tk.Tk, largura: int = 500, altura: int = 300) -> None:
    """
    Centraliza a janela na tela
    
    Args:
        root: Widget raiz da janela
        largura: Largura da janela
        altura: Altura da janela
    """
    # Pega a largura e altura da tela
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()

    # Calcula as coordenadas para centralizar
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)

    # Define a geometria da janela
    root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

def configurar_estilo_janela(root: tk.Tk, titulo: str, largura: int = 500, altura: int = 300) -> None:
    """
    Configura uma janela com título e centralização
    
    Args:
        root: Widget raiz da janela
        titulo: Título da janela
        largura: Largura da janela
        altura: Altura da janela
    """
    root.title(titulo)
    centralizar_janela(root, largura, altura)
    root.resizable(False, False)  # Janela não redimensionável

def criar_frame_centralizado(parent: tk.Widget, padding: int = 10) -> tk.Frame:
    """
    Cria um frame centralizado com padding
    
    Args:
        parent: Widget pai
        padding: Padding do frame
        
    Returns:
        Frame configurado
    """
    frame = tk.Frame(parent, padx=padding, pady=padding)
    frame.pack(expand=True, fill=tk.BOTH)
    return frame

def configurar_estilo_ttk() -> None:
    """
    Configura estilos personalizados para ttk
    """
    from tkinter import ttk
    
    style = ttk.Style()
    style.configure("Custom.TFrame", background="#f0f0f0")
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
    style.configure("Status.TLabel", font=("Segoe UI", 9), padding=5)
    style.configure("Custom.TButton", font=("Segoe UI", 9), padding=5) 