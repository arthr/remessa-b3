# src/services/backup_service.py
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import re
import os

class BackupService:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def criar_backup(self, arquivo_original: str, bordero: str) -> Optional[str]:
        """Cria backup do arquivo gerado"""
        try:
            # Garantir que o nome do arquivo seja seguro para o sistema de arquivos
            bordero_seguro = re.sub(r'[^\w\-_]', '_', bordero)
            
            # Obter a extensão do arquivo original
            _, ext = os.path.splitext(arquivo_original)
            
            # Criar nome do arquivo de backup com timestamp para evitar sobrescrever
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{bordero_seguro}_{timestamp}{ext}"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(arquivo_original, backup_path)
            return str(backup_path)
        except Exception as e:
            # TODO: Implementar envio de erro para interface
            #atualizar_status(f"Erro ao criar backup: {e}", "error")
            print(f"Erro ao criar backup: {e}")
            return None

    def listar_backups(self) -> List[Path]:
        """Lista todos os backups disponíveis"""
        return list(self.backup_dir.glob("*"))
