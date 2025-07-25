# src/utils/validation.py
from typing import List

def validar_bordero(bordero: str) -> bool:
    """Valida se o borderô contém apenas dígitos"""
    return bordero.isdigit()

def validar_lista_borderos(borderos: List[str]) -> List[str]:
    """Valida uma lista de borderôs e retorna os válidos"""
    return [b for b in borderos if validar_bordero(b)]

def validar_carteira_id(carteira_id: int) -> bool:
    """Valida se o ID da carteira é válido"""
    return carteira_id in [0, 2]  # Carteira Própria = 0, Carteira FIDC = 2

def validar_arquivo_saida(caminho: str) -> bool:
    """Valida se o caminho do arquivo de saída é válido"""
    from pathlib import Path
    try:
        path = Path(caminho)
        return path.parent.exists() or path.parent == Path('.')
    except Exception:
        return False