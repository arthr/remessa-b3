# src/models/update/download_result.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class DownloadResult:
    """Resultado de um download de atualização"""
    sucesso: bool
    filepath: Optional[str] = None
    erro: Optional[str] = None