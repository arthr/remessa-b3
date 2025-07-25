# src/services/update_service.py
from typing import List, Dict
from ..config.constants import AppConstants
from ..config.settings import Settings
import requests
from packaging import version

class UpdateService:
    def __init__(self):
        self.constants = AppConstants()
        self.settings = Settings()
    
    def verificar_atualizacao(self) -> bool:
        """Verifica se há atualizações disponíveis"""
        try:
            headers = {}
            if self.settings.github_token:
                headers["Authorization"] = f"token {self.settings.github_token}"
                
            response = requests.get(self.settings.github_api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                dados = response.json()
                ultima_versao = dados.get('tag_name', '').lstrip('v')
                
                if version.parse(ultima_versao) > version.parse(self.settings.app_version):
                    assets = dados.get('assets', [])
                    download_url = None
                    for asset in assets:
                        if asset.get('name', '').endswith('.exe'):
                            download_url = asset.get('browser_download_url')
                            break

                    return {
                        'disponivel': True,
                        'versao': ultima_versao,
                        'url': dados.get('html_url', ''),
                        'download_url': download_url,
                        'notas': dados.get('body', 'Notas de lançamento não disponíveis.')
                    }
            return {'disponivel': False}
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return {'disponivel': False}
    
    def baixar_atualizacao(self) -> bool:
        """Baixa a atualização"""
        # Lógica do baixar_atualizacao()
        pass

    def instalar_atualizacao(self) -> bool:
        """Instala a atualização"""
        # Lógica do instalar_atualizacao()
        pass
