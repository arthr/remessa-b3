# src/ui/splash_screen.py
import tkinter as tk
from tkinter import ttk, Canvas
from PIL import Image, ImageTk
from ..config.constants import AppConstants
from ..utils.path_utils import resource_path

class SplashScreen:
    def __init__(self, parent):
        self.parent = parent
        self.constants = AppConstants()
        self.splash = None
        self.canvas = None
        self.progress_var = None
        self.progress = None
        self.status_text = None
        self.tk_image = None
        
        self.setup_splash()
    
    def setup_splash(self):
        """Configura a splash screen"""
        if not self.parent:
            return
            
        self.splash = tk.Toplevel(self.parent)
        self.splash.title("Carregando...")
        self.splash.overrideredirect(True)  # Remove bordas da janela
        
        # Configurar a janela para ficar no topo
        self.splash.attributes("-topmost", True)
        
        # Carregar a imagem de splash
        try:
            # Usar resource_path para encontrar o caminho correto da imagem
            splash_image_path = resource_path("splashLogo.png")
            splash_image = Image.open(splash_image_path)
            # Obter dimensões da imagem
            width, height = splash_image.size
            
            # Configurar a geometria da janela
            screen_width = self.splash.winfo_screenwidth()
            screen_height = self.splash.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.splash.geometry(f"{width}x{height}+{x}+{y}")
            
            # Criar um canvas com fundo transparente
            self.canvas = Canvas(self.splash, width=width, height=height, 
                                bg='#f0f0f0', highlightthickness=0)
            self.canvas.pack()
            
            # Converter a imagem para formato Tkinter
            self.tk_image = ImageTk.PhotoImage(splash_image)
            
            # Adicionar a imagem ao canvas
            self.canvas.create_image(width//2, height//2, image=self.tk_image)
            
            # Adicionar texto de versão
            self.canvas.create_text(width//2, height-20, 
                                   text=f"Versão {self.constants.APP_VERSION}", 
                                   fill="#333333", font=("Segoe UI", 10))
            
            # Adicionar barra de progresso
            self.progress_var = tk.DoubleVar()
            self.progress = ttk.Progressbar(self.splash, variable=self.progress_var, 
                                          length=width-40, mode="determinate")
            self.progress_window = self.canvas.create_window(width//2, height-40, 
                                                          window=self.progress)
            
            # Adicionar texto de status
            self.status_text = self.canvas.create_text(width//2, height-60, 
                                                    text="Inicializando...", 
                                                    fill="#333333", font=("Segoe UI", 9))
        except Exception as e:
            print(f"Erro ao carregar splash screen: {e}")
            if self.splash:
                self.splash.destroy()
    
    def update_progress(self, value: int, status_text: str):
        """Atualiza o progresso e o texto de status"""
        if not self.splash or not self.progress_var or not self.canvas or not self.status_text:
            return
            
        self.progress_var.set(value)
        self.canvas.itemconfig(self.status_text, text=status_text)
        self.splash.update_idletasks()
    
    def destroy(self):
        """Fecha a splash screen"""
        if self.splash:
            self.splash.destroy()