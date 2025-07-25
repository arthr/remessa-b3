# src/database/connection.py
import pyodbc
from typing import Optional, List, Dict, Any
from ..config.settings import Settings
from ..utils.config_utils import verificar_configuracoes_banco

class DatabaseConnection:
    def __init__(self):
        self.settings = Settings()
    
    def connect(self) -> Optional[pyodbc.Connection]:
        try:
            config_ok, config_msg = verificar_configuracoes_banco(self.settings)
            if not config_ok:
                raise ValueError(f"Credenciais de banco de dados incompletas. {config_msg}")
            
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.settings.db_server};"
                f"DATABASE={self.settings.db_name};"
                f"UID={self.settings.db_user};"
                f"PWD={self.settings.db_password}"
            )
            return conn
        except Exception as e:
            raise ConnectionError(f"Erro ao conectar ao banco: {e}")

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executa uma query no banco de dados"""
        try:
            conn = self.connect()
            if not conn:
                raise ConnectionError("Não foi possível conectar ao banco de dados")
                
            cursor = conn.cursor()
            
            # Executar query com ou sem parâmetros
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Obter colunas
            columns = [desc[0] for desc in cursor.description]
            
            # Converter para lista de dicionários
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            
            # Fechar conexão
            conn.close()
            
            return result
            
        except Exception as e:
            raise Exception(f"Erro ao executar query: {e}")

    # TODO: Implementar em um futuro próximo
    # def execute_query_result(self, query_result: QueryResult) -> List[Dict[str, Any]]:
    #     """Executa uma QueryResult diretamente"""
    #     return self.execute_query(query_result.sql, query_result.params)