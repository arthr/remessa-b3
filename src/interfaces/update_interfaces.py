# src/interfaces/update_interfaces.py
from typing import Protocol, Optional, Callable
from ..models.update import UpdateInfo, DownloadResult, UpdateProgress

class UpdateChecker(Protocol):
    """Interface para verificação de atualizações"""
    def check_for_updates(self) -> UpdateInfo: ...

class UpdateDownloader(Protocol):
    """Interface para download de atualizações"""
    def download_update(self, url: str, version: str, 
                       progress_callback: Optional[Callable[[UpdateProgress], None]] = None) -> DownloadResult: ...

class UpdateInstaller(Protocol):
    """Interface para instalação de atualizações"""
    def install_update(self, file_path: str, app_exec: str) -> bool: ...