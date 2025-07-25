# src/config/settings.py
import os
import sys
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        self._load_environment()
    
    # Carrega as variáveis de ambiente
    def _load_environment(self):
        load_dotenv()
        if getattr(sys, 'frozen', False):
            executable_dir = os.path.dirname(sys.executable)
            env_path = os.path.join(executable_dir, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
            else:
                try:
                    base_path = sys._MEIPASS
                    env_path = os.path.join(base_path, '.env')
                    if os.path.exists(env_path):
                        load_dotenv(env_path)
                except Exception:
                    pass
    
    # Configurações da aplicação
    @property
    def app_version(self):
        return os.getenv("APP_VERSION", "1.1.0")
    
    @property
    def app_name(self):
        return os.getenv("APP_NAME", "Remessa B3")

    # Configurações do GitHub
    @property
    def github_repo(self):
        return os.getenv("GITHUB_REPO", "arthr/remessa-b3")
    
    @property
    def github_api_url(self):
        return f"https://api.github.com/repos/{self.github_repo}/releases/latest"
    
    @property
    def github_token(self):
        return os.getenv("GITHUB_TOKEN", "")

    # Configurações do banco de dados
    @property
    def db_server(self):
        return os.getenv("DB_SERVER", "")
    
    @property
    def db_name(self):
        return os.getenv("DB_NAME", "")

    @property
    def db_user(self):
        return os.getenv("DB_USER", "")
    
    @property
    def db_password(self):
        return os.getenv("DB_PASSWORD", "")

    # Configurações de carteira
    @property
    def carteira_fidc_id(self):
        return int(os.getenv("CARTEIRA_FIDC_ID", "2"))
    
    @property
    def carteira_propria_id(self):
        return int(os.getenv("CARTEIRA_PROPRIA_ID", "0"))

    # Configurações de conta
    @property
    def conta_escriturador(self):
        return os.getenv("CONTA_ESCRITURADOR", "58561405")
    
    @property
    def cnpj_titular(self):
        return os.getenv("CNPJ_TITULAR", "51030944000142")

    @property
    def razao_titular(self):
        return os.getenv("RAZAO_TITULAR", "DIRETA CAPITAL FIDC")
