# test_update_system.py
import sys
import os

# Adicionar o diretório src ao path (como no app.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar diretamente os módulos necessários
from src.services.update_service import UpdateService
from src.models.update import UpdateInfo

def test_update_system():
    print("Testando sistema de atualização...")
    
    try:
        # Criar UpdateService
        update_service = UpdateService()
        
        # Verificar atualizações
        print("Verificando atualizações...")
        update_info = update_service.check_for_updates()
        
        print(f"Atualização disponível: {update_info.disponivel}")
        if update_info.disponivel:
            print(f"Versão: {update_info.versao}")
            print(f"URL: {update_info.url}")
            print(f"Download URL: {update_info.download_url}")
        
        print("Teste concluído!")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_update_system()