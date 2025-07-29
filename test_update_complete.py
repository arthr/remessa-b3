#!/usr/bin/env python3
"""
Script de teste para validar o sistema de atualização completo
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_update_system():
    """Testa o sistema de atualização completo"""
    print("=== Teste do Sistema de Atualização ===")
    
    try:
        # Teste 1: Importar UpdateService
        print("1. Testando importação do UpdateService...")
        from src.services.update_service import UpdateService
        print("   ✅ UpdateService importado com sucesso")
        
        # Teste 2: Criar instância
        print("2. Testando criação da instância...")
        update_service = UpdateService()
        print("   ✅ Instância criada com sucesso")
        
        # Teste 3: Verificar atualizações
        print("3. Testando verificação de atualizações...")
        update_info = update_service.check_for_updates()
        print(f"   ✅ Verificação concluída: {update_info.disponivel}")
        
        # Teste 4: Importar modelos
        print("4. Testando importação dos modelos...")
        from src.models.update import UpdateInfo, DownloadResult, UpdateProgress
        print("   ✅ Modelos importados com sucesso")
        
        # Teste 5: Importar interfaces
        print("5. Testando importação das interfaces...")
        from src.interfaces.update_interfaces import UpdateChecker, UpdateDownloader, UpdateInstaller
        print("   ✅ Interfaces importadas com sucesso")
        
        # Teste 6: Verificar se UpdateService implementa as interfaces
        print("6. Testando implementação das interfaces...")
        assert isinstance(update_service, UpdateChecker)
        assert isinstance(update_service, UpdateDownloader)
        assert isinstance(update_service, UpdateInstaller)
        print("   ✅ UpdateService implementa todas as interfaces")
        
        print("\n=== Todos os testes passaram! ===")
        print("Sistema de atualização está funcionando corretamente.")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_update_system()
    sys.exit(0 if success else 1) 