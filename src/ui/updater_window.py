# src/ui/updater_window.py
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from ..config.settings import Settings
from ..services.update_service import UpdateService
from ..models.update import UpdateProgress
from ..utils import centralizar_janela

class UpdaterWindow:
    def __init__(self, parent, download_url, versao, app_exec, update_service: UpdateService):
        self.parent = parent
        self.settings = Settings()
        
        self.root = ThemedTk(theme="azure")
        self.root.title(f"{self.settings.app_name} - Updater")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.download_url = download_url
        self.versao = versao
        self.app_exec = app_exec
        self.update_service = update_service

        self.arquivo_baixado = None
    
    def run(self):
        # Centralizar janela
        centralizar_janela(self.root, 500, 300)
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(self.main_frame, text="Atualizando o Sistema", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Informações da versão
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.info_frame, text=f"Baixando a versão: {self.versao}").pack(anchor="w", pady=2)
        
        # Barra de progresso
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                           length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Iniciando download...")
        self.progress_label.pack(anchor="w", pady=2)
        
        # Frame de status
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Aguardando...")
        self.status_label.pack(anchor="w", pady=2)
        
        # Botões
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.cancelar_btn = ttk.Button(self.button_frame, text="Cancelar", 
                                      command=self.cancelar_download)
        self.cancelar_btn.pack(side=tk.RIGHT, padx=5)
        
        # Iniciar automaticamente o download quando a interface estiver pronta
        self.root.after(500, self.iniciar_download)

        self.root.mainloop()
    
    def atualizar_progresso(self, progress: UpdateProgress):
        """Atualiza a barra de progresso e exibe a velocidade"""
        self.progress_var.set(progress.porcentagem)
        texto = f"Baixando: {progress.porcentagem}%"
        if progress.velocidade:
            texto += f" ({progress.velocidade})"
        self.progress_label.config(text=texto)
    
    def iniciar_download(self):
        """Inicia o download da atualização"""
        if not self.download_url:
            self.atualizar_status("URL de download inválida!")
            return
        
        # Iniciar o download
        self.atualizar_status("Iniciando download da nova versão...")
        threading.Thread(target=self.update_service.download_update, args=(self.download_url, self.versao, self.atualizar_progresso), daemon=True).start()
    
    def download_finalizado(self, filepath):
        """Chamado quando o download é concluído"""
        if filepath:
            self.arquivo_baixado = filepath
        else:
            self.arquivo_baixado = None

        self.atualizar_status("Download concluído com sucesso!")
        self.progress_label.config(text="Download concluído!")
        
        # Modificar botão para instalar
        self.cancelar_btn.config(text="Instalar Agora", command=lambda: self.install_update(self.arquivo_baixado, self.app_exec))
    
    def install_update(self, arquivo_baixado, app_exec):
        """Instala a atualização substituindo o executável atual"""
        installed = self.update_service.install_update(arquivo_baixado, app_exec)
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
        """Cancela o download e fecha a aplicação"""
        if messagebox.askyesno("Cancelar Download", "Deseja realmente cancelar a atualização?"):
            self.root.destroy()
    
    def destroy(self):
        """Destrói a janela"""
        if self.root:
            self.root.destroy()
