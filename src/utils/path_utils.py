# src/utils/path_utils.py
import os
import sys
from pathlib import Path
from typing import Union

def resource_path(relative_path: Union[str, Path]) -> str:
    """
    Obter o caminho absoluto para o recurso, funcionando para dev e para PyInstaller
    
    Args:
        relative_path: Caminho relativo do recurso
        
    Returns:
        Caminho absoluto do recurso
    """
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, str(relative_path))

def get_executable_dir() -> str:
    """
    Obtém o diretório do executável atual
    
    Returns:
        Caminho do diretório do executável
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

def get_base_path() -> str:
    """
    Obtém o caminho base da aplicação (desenvolvimento ou executável)
    
    Returns:
        Caminho base da aplicação
    """
    try:
        return sys._MEIPASS
    except Exception:
        return os.path.abspath(".")

def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Garante que um diretório existe, criando-o se necessário
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        Path do diretório
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path 