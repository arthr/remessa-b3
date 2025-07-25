# src/utils/text_utils.py
import unicodedata
import re

def remover_acentos(texto: str) -> str:
    """Remove acentos de um texto"""
    normalizado = unicodedata.normalize("NFD", texto)
    return ''.join(char for char in normalizado if unicodedata.category(char) != 'Mn')

def limpar_numeros(texto: str) -> str:
    """Remove caracteres não numéricos"""
    return re.sub(r'\D', '', texto)