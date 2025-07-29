# src/interfaces/update_interfaces.py
from typing import Protocol, Optional, Callable, runtime_checkable
from ..models.update import UpdateInfo, DownloadResult, UpdateProgress

@runtime_checkable
class UpdateChecker(Protocol):
    """Interface para verificação de atualizações"""
    def check_for_updates(self) -> UpdateInfo: ...

@runtime_checkable
class UpdateDownloader(Protocol):
    """Interface para download de atualizações"""
    def download_update(self, url: str, version: str, 
                       progress_callback: Optional[Callable[[UpdateProgress], None]] = None) -> DownloadResult: ...

@runtime_checkable
class UpdateInstaller(Protocol):
    """Interface para instalação de atualizações"""
    def install_update(self, file_path: str, app_exec: str) -> bool: ...