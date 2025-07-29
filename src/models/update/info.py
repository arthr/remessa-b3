# src/models/update/info.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class UpdateInfo:
    """Informações sobre uma atualização disponível"""
    disponivel: bool
    versao: Optional[str] = None
    url: Optional[str] = None
    download_url: Optional[str] = None
    notas: Optional[str] = None
