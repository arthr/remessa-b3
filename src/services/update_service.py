# src/services/update_service.py

from typing import Dict, Any, Optional, Callable
import requests
from packaging import version
import threading
import time
from pathlib import Path
import os
import subprocess
import sys
from ..config.constants import AppConstants
from ..config.settings import Settings
from ..interfaces.update_interfaces import UpdateChecker, UpdateDownloader, UpdateInstaller
from ..models.update import UpdateInfo, DownloadResult, UpdateProgress

class UpdateService(UpdateChecker, UpdateDownloader, UpdateInstaller):
    def __init__(self):
        self.constants = AppConstants()
        self.settings = Settings()
        self.update_info = UpdateInfo(disponivel=False)

    def check_for_updates(self) -> UpdateInfo:
        """Verifica se há atualizações"""
        try:
            headers = {}
            if self.settings.github_token:
                headers["Authorization"] = f"token {self.settings.github_token}"
                
            response = requests.get(self.settings.github_api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                dados = response.json()
                ultima_versao = dados.get('tag_name', '').lstrip('v')
                
                if version.parse(ultima_versao) > version.parse(self.settings.app_version):
                    assets = dados.get('assets', [])
                    download_url = None
                    for asset in assets:
                        if asset.get('name', '').endswith('.exe'):
                            download_url = asset.get('browser_download_url')
                            break

                    self.update_info = UpdateInfo(
                        disponivel=True,
                        versao=ultima_versao,
                        url=dados.get('html_url', ''),
                        download_url=download_url,
                        notas=dados.get('body', 'Notas de lançamento não disponíveis.')
                    )
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            self.update_info = UpdateInfo(disponivel=False)
        
        return self.update_info

    def get_update_info(self) -> UpdateInfo:
        return self.update_info

    def run_updater(self, download_url: str, versao: str, app_exec: str) -> None:
        """Executa o updater.py"""
        if not getattr(sys, 'frozen', False):
            subprocess.Popen([
                sys.executable, "updater.py", 
                download_url, versao, app_exec
            ])
        else:
            subprocess.Popen(["updater.exe", download_url, versao, app_exec])

    def download_update(self, download_url: str, versao: str, 
                       progress_callback: Optional[Callable[[UpdateProgress], None]] = None) -> DownloadResult:
        """Baixa a atualização com progresso e velocidade"""
        def _download_task():
            try:
                # Criar pasta de atualizações
                updates_dir = Path("updates")
                updates_dir.mkdir(exist_ok=True)
                
                # Nome do arquivo
                filename = f"remessa-b3-v{versao}.exe"
                filepath = updates_dir / filename
                
                # Headers para download
                headers = {'Accept': 'application/octet-stream'}
                
                # Download com progresso
                response = requests.get(download_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_time = time.time()
                last_downloaded = 0
                
                with open(filepath, 'wb') as f:
                    for data in response.iter_content(1024 * 8):
                        f.write(data)
                        downloaded += len(data)
                        
                        # Calcular velocidade a cada 0.5s
                        current_time = time.time()
                        if current_time - last_time > 0.5 or downloaded == total_size:
                            elapsed = current_time - last_time
                            chunk_size = downloaded - last_downloaded
                            speed = chunk_size / elapsed if elapsed > 0 else 0
                            
                            # Formatar velocidade
                            if speed > 1048576:
                                speed_text = f"{speed/1048576:.1f} MB/s"
                            else:
                                speed_text = f"{speed/1024:.1f} KB/s"
                            
                            # Callback de progresso
                            if total_size > 0 and progress_callback:
                                progress = UpdateProgress(
                                    porcentagem=int((downloaded / total_size) * 100),
                                    velocidade=speed_text,
                                    bytes_baixados=downloaded,
                                    bytes_total=total_size
                                )
                                progress_callback(progress)
                            
                            last_time = current_time
                            last_downloaded = downloaded
                
                # Retornar resultado
                return DownloadResult(sucesso=True, filepath=str(filepath))
                    
            except Exception as e:
                return DownloadResult(sucesso=False, erro=str(e))
        
        # Executar em thread separada e retornar resultado
        result = [None]
        def _run_and_capture():
            result[0] = _download_task()
        
        thread = threading.Thread(target=_run_and_capture, daemon=True)
        thread.start()
        thread.join()
        
        return result[0] if result[0] else DownloadResult(sucesso=False, erro="Erro desconhecido")
    
    def install_update(self, arquivo_path: str, app_exec: str) -> bool:
        """Instala a atualização"""
        try:
            if not app_exec:
                return False
                
            if os.name == 'nt':
                # Criar arquivo de sinalização
                signal_file = Path("updates") / "update_ready.signal"
                with open(signal_file, 'w') as f:
                    f.write("ready")
                
                # Criar script batch
                updater_script = Path("updates") / "updater.bat"
                with open(updater_script, 'w') as f:
                    f.write('@echo off\n')
                    f.write('echo Aguardando o encerramento da aplicacao...\n')
                    f.write(f'ping -n 3 127.0.0.1 > nul\n')  # Esperar ~3 segundos
                    f.write('echo Instalando atualizacao...\n')
                    # Tentar copiar várias vezes caso o arquivo esteja em uso
                    f.write(':retry\n')
                    f.write(f'copy /Y "{arquivo_path}" "{app_exec}" > nul\n')
                    f.write('if errorlevel 1 (\n')
                    f.write('    echo Erro na atualizacao, tentando novamente...\n')
                    f.write('    ping -n 2 127.0.0.1 > nul\n')
                    f.write('    goto retry\n')
                    f.write(')\n')
                    f.write('echo Atualizacao concluida!\n')
                    f.write(f'start "" "{app_exec}"\n')  # Iniciar a nova versão
                    f.write('del "%~f0"\n')  # Auto-destruir o script
                
                # Executar script
                subprocess.Popen(['cmd', '/c', str(updater_script)], 
                               shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.check_update_signal()
                return True
            else:
                return False
        except Exception as e:
            print(f"Erro na instalação: {e}")
            return False
    
    def check_update_signal(self) -> bool:
        """Verifica se o sinal de atualização existe"""
        signal_file = Path("updates") / "update_ready.signal"
        if signal_file.exists():
            signal_file.unlink()
            return True
        return False