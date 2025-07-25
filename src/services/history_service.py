# src/services/history_service.py
from typing import List, Dict
import json
from pathlib import Path
from datetime import datetime
from src.config.constants import AppConstants

class HistoryService:
    def __init__(self):
        self.constants = AppConstants()
        self.historico_operacoes = []
        self.carregar_historico()
    
    def carregar_historico(self) -> List[Dict]:
        """Carrega o histórico de operações do arquivo JSON"""
        try:
            if Path(self.constants.HISTORY_FILE).exists():
                with open(self.constants.HISTORY_FILE, "r") as f:
                    self.historico_operacoes = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
        return self.historico_operacoes

    def salvar_historico(self) -> None:
        """Salva o histórico de operações em um arquivo JSON"""
        try:
            with open(self.constants.HISTORY_FILE, "w") as f:
                json.dump(self.historico_operacoes, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")

    def adicionar_historico(self, operacao: str) -> None:
        """Adiciona uma operação ao histórico"""
        self.historico_operacoes.append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "operacao": operacao
        })
        self.salvar_historico()
    
    def limpar_historico(self) -> None:
        """Limpa o histórico de operações"""
        self.historico_operacoes = []
        self.salvar_historico()
