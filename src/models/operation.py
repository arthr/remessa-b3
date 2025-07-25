# src/models/operation.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Operation:
    data: datetime
    tipo: str
    descricao: str
    arquivo_gerado: Optional[str] = None
    borderos_processados: Optional[List[str]] = None