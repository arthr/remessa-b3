# src/updater/updater_window.py
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from config.settings import Settings
from services.update_service import UpdateService
from utils import centralizar_janela

class UpdaterWindow:
    def __init__(self, parent, download_url, versao, app_exec):
        self.parent = parent
        self.download_url = download_url
        self.versao = versao
        self.app_exec = app_exec
        self.arquivo_baixado = None
        
        self.root = ThemedTk(theme="azure")
        self.settings = Settings()
        self.update_service = UpdateService()
        
        self.root.title(f"{self.settings.app_name} - Updater")
        self.root.geometry("500x400")
        centralizar_janela(self.root, 500, 400)
        
        self.setup_ui()
        self.root.after(500, self.iniciar_download)
    
    def setup_ui(self):
        """Configura a interface da janela"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Atualizando o Sistema", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Informações da versão
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Baixando a versão: {self.versao}").pack(anchor="w", pady=2)
        
        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Iniciando download...")
        self.progress_label.pack(anchor="w", pady=2)
        
        # Frame de status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Aguardando...")
        self.status_label.pack(anchor="w", pady=2)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.cancelar_btn = ttk.Button(button_frame, text="Cancelar", 
                                      command=self.cancelar_download)
        self.cancelar_btn.pack(side=tk.RIGHT, padx=5)
    
    def atualizar_progresso(self, porcentagem, velocidade=""):
        """Atualiza a barra de progresso e exibe a velocidade"""
        self.progress_var.set(porcentagem)
        texto = f"Baixando: {porcentagem}%"
        if velocidade:
            texto += f" ({velocidade})"
        self.progress_label.config(text=texto)
    
    def iniciar_download(self):
        """Inicia o download da atualização"""
        if not self.download_url:
            self.atualizar_status("URL de download inválida!")
            return
        
        self.atualizar_status("Iniciando download da nova versão...")
        
        def progress_callback(progress):
            self.atualizar_progresso(progress.porcentagem, progress.velocidade)
        
        def download_complete():
            result = self.update_service.download_update(
                self.download_url, 
                self.versao, 
                progress_callback
            )
            if result.sucesso:
                self.download_finalizado(result.filepath)
            else:
                self.download_finalizado(None)
        
        threading.Thread(target=download_complete, daemon=True).start()
    
    def download_finalizado(self, filepath):
        """Chamado quando o download é concluído"""
        if filepath:
            self.arquivo_baixado = filepath
            self.atualizar_status("Download concluído com sucesso!")
            self.progress_label.config(text="Download concluído!")
            self.cancelar_btn.config(text="Instalar Agora", 
                                   command=self.install_update)
        else:
            self.atualizar_status("Erro no download!")
    
    def install_update(self):
        """Instala a atualização"""
        if not self.arquivo_baixado:
            self.atualizar_status("Erro: Nenhum arquivo baixado!")
            return
            
        installed = self.update_service.install_update(self.arquivo_baixado, self.app_exec)
        if installed:
            self.atualizar_status("Atualização instalada com sucesso!")
            self.root.quit()
        else:
            self.atualizar_status("Erro ao instalar a atualização!")
    
    def atualizar_status(self, mensagem):
        """Atualiza a mensagem de status"""
        self.status_label.config(text=mensagem)
        self.root.update_idletasks()
    
    def cancelar_download(self):
        """Cancela o download"""
        self.atualizar_status("Download cancelado pelo usuário")
        self.root.quit()
    
    def run(self):
        """Inicia o loop principal"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Erro no updater window: {e}")
        finally:
            # Garantir encerramento limpo
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
    
    def destroy(self):
        """Destrói a janela de forma limpa"""
        try:
            if self.root:
                self.root.quit()
                self.root.destroy()
        except:
            pass 