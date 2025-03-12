import sys
import os
import requests
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess
import json

# Informações da aplicação
APP_NAME = "Remessa B3"

# Variáveis globais
download_url = None
versao = None
destino = None
app_exec = None
download_concluido = False
arquivo_baixado = None

class UpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - Atualizador")
        self.root.geometry("500x400")
        
        # Centralizar janela
        self.centralizar_janela()
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(self.main_frame, text="Atualizando o Sistema", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Informações da versão
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.info_frame, text=f"Baixando a versão: {versao}").pack(anchor="w", pady=2)
        
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
    
    def centralizar_janela(self):
        """Centraliza a janela na tela."""
        largura = 500
        altura = 400
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    
    def atualizar_progresso(self, porcentagem, velocidade=""):
        """Atualiza a barra de progresso e exibe a velocidade"""
        self.progress_var.set(porcentagem)
        texto = f"Baixando: {porcentagem}%"
        if velocidade:
            texto += f" ({velocidade})"
        self.progress_label.config(text=texto)
    
    def iniciar_download(self):
        """Inicia o download da atualização"""
        global download_url, versao, destino
        
        if not download_url:
            self.atualizar_status("URL de download inválida!")
            return
        
        # Iniciar o download
        self.atualizar_status("Iniciando download da nova versão...")
        threading.Thread(target=self.baixar_atualizacao, daemon=True).start()
    
    def baixar_atualizacao(self):
        """
        Baixa a atualização
        """
        global download_url, versao, download_concluido, arquivo_baixado
        
        try:
            # Criar pasta de atualizações se não existir
            updates_dir = Path("updates")
            if not updates_dir.exists():
                updates_dir.mkdir()
            
            # Nome do arquivo de destino
            filename = f"remessa-b3-v{versao}.exe"
            filepath = updates_dir / filename
            
            # Configurar headers com token se disponível
            headers = {
                'Accept': 'application/octet-stream'  # Necessário para download de binários no GitHub
            }
            
            # Realizar o download com relatório de progresso
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Obter o tamanho total do arquivo
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 8  # 8 KiB por bloco
            downloaded = 0
            
            # Variáveis para calcular velocidade
            start_time = time.time()
            last_time = start_time
            last_downloaded = 0
            
            with open(filepath, 'wb') as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded += len(data)
                    
                    # Calcular progresso e velocidade a cada 0.5 segundos
                    current_time = time.time()
                    if current_time - last_time > 0.5 or downloaded == total_size:
                        # Calcular velocidade em KB/s
                        elapsed = current_time - last_time
                        chunk_size = downloaded - last_downloaded
                        speed = chunk_size / elapsed if elapsed > 0 else 0
                        
                        # Converter para unidade apropriada
                        speed_text = ""
                        if speed > 1048576:  # 1 MB/s
                            speed_text = f"{speed/1048576:.1f} MB/s"
                        else:
                            speed_text = f"{speed/1024:.1f} KB/s"
                        
                        # Atualizar progresso
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            # Chamada de progresso na thread principal
                            self.root.after(0, lambda p=progress, s=speed_text: self.atualizar_progresso(p, s))
                        
                        # Atualizar variáveis para próxima iteração
                        last_time = current_time
                        last_downloaded = downloaded
            
            # Download concluído
            download_concluido = True
            arquivo_baixado = str(filepath)
            self.root.after(0, self.download_finalizado)
            
        except Exception as e:
            self.root.after(0, lambda: self.atualizar_status(f"Erro no download: {e}"))
    
    def download_finalizado(self):
        """Chamado quando o download é concluído"""
        global arquivo_baixado
        
        self.atualizar_status("Download concluído com sucesso!")
        self.progress_label.config(text="Download concluído!")
        
        # Modificar botão para instalar
        self.cancelar_btn.config(text="Instalar Agora", command=self.instalar_atualizacao)
    
    def instalar_atualizacao(self):
        """Instala a atualização substituindo o executável atual"""
        global arquivo_baixado, app_exec
        
        try:
            self.atualizar_status("Preparando instalação...")
            
            # Obter o caminho do executável principal
            if not app_exec:
                self.atualizar_status("Erro: Caminho do executável principal não informado!")
                return
                
            # No Windows, criar um script para substituir o executável após o fechamento
            if os.name == 'nt':
                # Criar um arquivo de sinalização para a aplicação principal
                signal_file = Path("updates") / "update_ready.signal"
                with open(signal_file, 'w') as f:
                    f.write("ready")
                    
                # Criar um script batch para executar após o fechamento do aplicativo
                updater_script = Path("updates") / "updater.bat"
                with open(updater_script, 'w') as f:
                    f.write('@echo off\n')
                    f.write('echo Aguardando o encerramento da aplicacao...\n')
                    f.write(f'ping -n 3 127.0.0.1 > nul\n')  # Esperar ~3 segundos
                    f.write('echo Instalando atualizacao...\n')
                    # Tentar copiar várias vezes caso o arquivo esteja em uso
                    f.write(':retry\n')
                    f.write(f'copy /Y "{arquivo_baixado}" "{app_exec}" > nul\n')
                    f.write('if errorlevel 1 (\n')
                    f.write('    echo Erro na atualizacao, tentando novamente...\n')
                    f.write('    ping -n 2 127.0.0.1 > nul\n')
                    f.write('    goto retry\n')
                    f.write(')\n')
                    f.write('echo Atualizacao concluida!\n')
                    f.write(f'start "" "{app_exec}"\n')  # Iniciar a nova versão
                    f.write('del "%~f0"\n')  # Auto-destruir o script
                    
                # Executar o script e fechar a aplicação
                subprocess.Popen(['cmd', '/c', str(updater_script)], 
                                shell=True, 
                                creationflags=subprocess.CREATE_NEW_CONSOLE)
                
                # Informar e fechar o atualizador
                self.atualizar_status("Atualizando...")
                messagebox.showinfo("Atualizando", "A aplicação principal será encerrada e atualizada.")
                self.root.quit()
            else:
                # Para outros SOs, informar sobre a atualização
                messagebox.showwarning("Atualização", 
                                      "Atualização automática não suportada neste sistema. Substitua manualmente o arquivo.")
        except Exception as e:
            self.atualizar_status(f"Erro na atualização: {e}")
    
    def atualizar_status(self, mensagem):
        """Atualiza a mensagem de status"""
        self.status_label.config(text=mensagem)
        self.root.update_idletasks()
    
    def cancelar_download(self):
        """Cancela o download e fecha a aplicação"""
        if messagebox.askyesno("Cancelar Download", "Deseja realmente cancelar a atualização?"):
            self.root.destroy()

def main():
    """Função principal do atualizador"""
    global download_url, versao, app_exec
    
    # Verificar argumentos
    if len(sys.argv) < 4:
        print("Uso: updater.py <download_url> <versao> <app_executable>")
        return
    
    # Extrair argumentos
    download_url = sys.argv[1]
    versao = sys.argv[2]
    app_exec = sys.argv[3]
    
    # Iniciar interface
    root = tk.Tk()
    app = UpdaterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()