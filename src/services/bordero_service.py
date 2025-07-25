# src/services/bordero_service.py
from typing import List, Dict, Optional
from ..database.connection import DatabaseConnection
from ..database.queries import BorderoQueries
#from ..models.bordero import Bordero

class BorderoService:
    def __init__(self):
        self.db_connection = DatabaseConnection()
    
    def consultar_bordero(self, bordero: str, carteira_id: Optional[int] = None) -> List[Dict]:
        """Consulta dados de um borderô específico"""
        try:
            query = BorderoQueries.get_titulos_query(borderos=[bordero], carteira_id=carteira_id)
            return self.db_connection.execute_query(query)
        except Exception as e:
            raise Exception(f"Erro ao consultar borderô: {e}")
    
    def consulta_lote_borderos(self, borderos: List[str], carteira_id: Optional[int] = None) -> Dict[str, List[Dict]]:
        """Consulta múltiplos borderôs em lote"""
        try:
            query = BorderoQueries.get_titulos_query(borderos=borderos, carteira_id=carteira_id)
            return self.db_connection.execute_query(query)
        except Exception as e:
            raise Exception(f"Erro ao consultar lote de borderôs: {e}")