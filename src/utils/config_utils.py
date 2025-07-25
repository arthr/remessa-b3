# src/utils/config_utils.py
from typing import Tuple, Dict, Any
from ..config.settings import Settings
import sys
import os

def verificar_configuracoes_banco(settings: Settings) -> Tuple[bool, str]:
    """
    Verifica se as configurações do banco de dados estão carregadas corretamente
    
    Args:
        settings: Instância das configurações
        
    Returns:
        Tupla (sucesso, mensagem)
    """
    configs = {
        'DB_SERVER': settings.db_server,
        'DB_NAME': settings.db_name,
        'DB_USER': settings.db_user,
        'DB_PASSWORD': settings.db_password
    }
    
    # Verificar se alguma configuração está vazia
    configs_vazias = [k for k, v in configs.items() if not v]
    
    if configs_vazias:
        return False, f"Configurações não encontradas: {', '.join(configs_vazias)}"
    
    return True, "Configurações carregadas com sucesso"

def validar_configuracoes_completas(settings: Settings) -> Dict[str, Any]:
    """
    Valida todas as configurações da aplicação
    
    Args:
        settings: Instância das configurações
        
    Returns:
        Dicionário com status de cada configuração
    """
    validacoes = {
        'banco_dados': verificar_configuracoes_banco(settings),
        'github': bool(settings.github_repo),
        'carteiras': bool(settings.carteira_fidc_id is not None and settings.carteira_propria_id is not None),
        'layout_b3': bool(settings.conta_escriturador and settings.cnpj_titular and settings.razao_titular)
    }
    
    return validacoes

def obter_resumo_configuracoes(settings: Settings) -> str:
    """
    Obtém um resumo das configurações para debug
    
    Args:
        settings: Instância das configurações
        
    Returns:
        String com resumo das configurações
    """
    config_ok, config_msg = verificar_configuracoes_banco(settings)
    
    info = f"Status das Configurações:\n{config_msg}\n\n"
    info += f"DB_SERVER: {'✓' if settings.db_server else '✗'} {settings.db_server or 'Não configurado'}\n"
    info += f"DB_NAME: {'✓' if settings.db_name else '✗'} {settings.db_name or 'Não configurado'}\n"
    info += f"DB_USER: {'✓' if settings.db_user else '✗'} {settings.db_user or 'Não configurado'}\n"
    info += f"DB_PASSWORD: {'✓' if settings.db_password else '✗'} {'***' if settings.db_password else 'Não configurado'}\n\n"
    info += f"Executável: {'Sim' if getattr(sys, 'frozen', False) else 'Não'}\n"
    info += f"Diretório atual: {os.getcwd()}"
    
    return info 