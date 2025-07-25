# src/models/bordero.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Bordero:
    numero: str
    carteira_id: int
    data_operacao: datetime
    valor_total: float
    situacao: str
    titulos: List['Titulo'] = None
    
    def __post_init__(self):
        if self.titulos is None:
            self.titulos = []

@dataclass
class Titulo:
    numero: str
    devedor: str
    valor: float
    vencimento: datetime
    situacao: str