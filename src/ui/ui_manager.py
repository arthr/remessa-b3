# src/ui/ui_manager.py
import tkinter as tk
from tkinter import messagebox
from ..interfaces.ui_interfaces import UIManager
from ..models.update import UpdateInfo
from .dialogs.update_available import UpdateAvailableDialog
from .updater_window import UpdaterWindow
from ..services.update_service import UpdateService

class UIManagerImpl(UIManager):
    def __init__(self, update_service: UpdateService):
        self.update_service = update_service
    
    def show_update_available_dialog(self, update_info: UpdateInfo) -> None:
        """Mostra diálogo de atualização disponível"""
        # Será implementado quando MainWindow for atualizada
        pass
    
    def show_download_progress_window(self, download_url: str, version: str, app_exec: str) -> None:
        """Mostra janela de progresso de download"""
        # Será implementado quando UpdaterWindow for refatorada
        pass
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """Mostra diálogo de erro"""
        messagebox.showerror(title, message)
    
    def show_info_dialog(self, title: str, message: str) -> None:
        """Mostra diálogo de informação"""
        messagebox.showinfo(title, message)
    
    def show_confirm_dialog(self, title: str, message: str) -> bool:
        """Mostra diálogo de confirmação"""
        return messagebox.askyesno(title, message) 