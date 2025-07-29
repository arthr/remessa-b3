# src/models/update/progress.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class UpdateProgress:
    """Progresso do download de atualização"""
    porcentagem: int
    velocidade: Optional[str] = None
    bytes_baixados: Optional[int] = None
    bytes_total: Optional[int] = None