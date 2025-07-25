# src/services/file_service.py
from typing import List, Dict
from datetime import datetime
from .history_service import HistoryService
from src.config.constants import AppConstants
from src.utils.text_utils import remover_acentos
import re
import os
import subprocess
import sys

class FileService:
    def __init__(self):
        self.constants = AppConstants()
        self.arquivo_gerado = None
        self.history_service = HistoryService()
    def gerar_header(self) -> str:
        tipo_if = "DC".ljust(5)  # Tipo IF
        tipo_registro = "0".ljust(1)  # Tipo de Registro
        acao = "INCL".ljust(4)  # Ação
        nome_participante = "DIRETACAPITAL".ljust(20)  # Nome Simplificado do Participante
        data_envio = datetime.now().strftime("%Y%m%d")  # Data no formato AAAAMMDD
        versao_layout = "00002".rjust(5)  # Versão do Layout (00001, 00002. Utilizando: 00002)
        delimitador = "<".ljust(1)  # Delimitador do Fim da Linha

        # Concatena os campos para formar o header
        header = (
            f"{tipo_if}"
            f"{tipo_registro}"
            f"{acao}"
            f"{nome_participante}"
            f"{data_envio}"
            f"{versao_layout}"
            f"{delimitador}"
        )
        return header
    
    def gerar_arquivo(self, dados: List[Dict], output_file: str) -> None:
        try:
            self.arquivo_gerado = output_file
            with open(output_file, "w") as f:
                f.write(self.gerar_header() + "\n")
                for row in dados:
                    linha = (
                        f"{row.get('Tipo_IF').ljust(5)}"  # Tipo IF
                        f"{row.get('Tipo_Registro', '1').ljust(1)}"  # Tipo de Registro
                        f"{row.get('Acao', 'INCL').ljust(4)}"  # Ação
                        f"{(row.get('Codigo_IF') or '').rjust(14)}"  # Código IF
                        f"{(row.get('Conta_Escriturador', self.constants.CONTA_ESCRITURADOR) or self.constants.CONTA_ESCRITURADOR).rjust(8)}"  # Conta Escriturador
                        f"{(row.get('Conta_do_Titular', '') or '').rjust(8)}"  # Conta do Titular
                        f"{re.sub(r'\D', '', (row.get('CNPJ_Titular', self.constants.CNPJ_TITULAR) or self.constants.CNPJ_TITULAR)).rjust(14)}"  # CPF/CNPJ do Titular
                        f"{remover_acentos(row.get('Razao_Titular', self.constants.RAZAO_TITULAR) or self.constants.RAZAO_TITULAR).ljust(100)}"  # Razão Social do Titular
                        f"{(row.get('Meu_Numero') or '').rjust(10)}"  # Meu Número
                        f"{(row.get('Manutencao') or '').rjust(2)}"  # Manutenção Unilateral
                        f"{(row.get('Tipo_Regime') or '2').ljust(1)}"  # Tipo de Regime
                        f"{re.sub(r'\D', '', (row.get('CNPJ_Credor', '0') or '0')).rjust(14)}"  # CPF/CNPJ do Credor
                        f"{remover_acentos(row.get('Razao_Credor') or 'RAZAO_CREDOR').ljust(100)}"  # Razão Social do Credor
                        f"{re.sub(r'\D', '', (row.get('CNPJ_Devedor', '0') or '0')).rjust(14)}"  # CPF/CNPJ do Devedor
                        f"{remover_acentos(row.get('Razao_Devedor') or 'RAZAO_DEVEDOR').ljust(100)}"  # Razão Social do Devedor
                        f"{re.sub(r'\D', '', str(row.get('Valor_Face', 0))).rjust(18, '0')}"  # Valor de Face
                        f"{re.sub(r'\D', '', str(row.get('Valor_Atualizado', 0))).rjust(18, '0')}"  # Valor Atualizado
                        f"{re.sub(r'\D', '', row.get('Data_Valor_Atualizado') or '').rjust(8)}"  # Data do Valor Atualizado
                        f"{re.sub(r'\D', '', row.get('Data_Emissao') or '').rjust(8)}"  # Data de Emissão
                        f"{re.sub(r'\D', '', row.get('Data_Vencimento') or '').rjust(8)}"  # Data de Vencimento
                        f"{re.sub(r'\D', '', row.get('Vencimento_Atualizada') or '').rjust(8)}"  # Data de Vencimento Atualizada
                        f"{(row.get('UF') or 'UF').rjust(2)}"  # UF da Praça de Pagamento
                        f"{remover_acentos(row.get('CIDADE') or 'CIDADE').rjust(40)}"  # Município da Praça de Pagamento
                        f"{(row.get('Especie_Titulo') or '02').rjust(2)}"  # Espécie de Título
                        f"{(row.get('Numero_Titulo') or '').rjust(10)}"  # Número do Título
                        f"{(row.get('Serie') or '').rjust(3)}"  # Série da Nota Fiscal
                        f"{(row.get('Numero') or '').rjust(9)}"  # Número da Nota Fiscal
                        f"{''.rjust(8)}"  # Data de Assinatura do Credor
                        f"{''.rjust(8)}"  # Data de Assinatura do Devedor
                        f"{''.ljust(100)}"  # Nome do Custodiante da Guarda Física (Opcional para INCL do tipo IF e DC)
                        f"{re.sub(r'\D', '', (str(row.get('Bordero')) + str(row.get('Numero_Titulo')))).rjust(40)}"  # Número de Controle Interno (Borderô + Núm. do Título)
                        f"{''.ljust(14)}"  # Código IF do Lote (Obrigatório apenas se DC for vinculado a um lote)
                        f"{(row.get('Chave') or '').ljust(44)}"  # Chave de Acesso/Código de Verificação (NF-e/NFS-e)
                        f"{('01' if row.get('Situacao') == 'PAGO' else '02').rjust(2)}"  # Status do Pagamento (01 - Pago, 02 - Em Aberto)
                        f"{'01'.rjust(2)}"  # Forma de Pagamento (01 - Boleto, 02 - TED, 03 - DOC, 04 - Dinheiro, 05 - Título)
                        f"{''.rjust(2)}"  # Tipo de Garantia (Opcional para INCL do tipo IF e DC | 01 - Aval)
                        f"{''.ljust(100)}"  # Nome do Garantidor (Opcional para INCL do tipo IF e DC)
                        f"{''.ljust(500)}"  # Descrição Adicional (Opcional para INCL do tipo IF e DC)
                        f"{re.sub(r'\D', '', str(row.get('Valor_nota_fiscal', 0))).rjust(18, '0')}"  # Valor Total da Nota Fiscal
                        f"{''.rjust(8)}"  # Taxa de Juros/Índice de Reajuste
                        f"{'0'.rjust(4, '0')}"  # Número de Parcelas
                        f"{''.rjust(7)}"  # Código do IBGE
                        f"{'N'.rjust(1)}"  # Operação Informada no SCR
                        f"{''.rjust(100)}"  # IPOC
                        f"<"  # Delimitador
                    )
                    f.write(linha + "\n")
        except Exception as e:
            # TODO: Implementar envio de erro para interface
            #messagebox.showerror("Erro na Exportação", f"Erro ao gerar o arquivo: {e}")
            print(f"Erro ao gerar o arquivo: {e}")

    def abrir_arquivo(self) -> None:
        if self.arquivo_gerado:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(self.arquivo_gerado)
                elif os.name == 'posix':  # macOS ou Linux
                    subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', self.arquivo_gerado))
                self.history_service.adicionar_historico(f"Arquivo aberto: {self.arquivo_gerado}")
            except Exception as e:
                # TODO: Implementar envio de erro para interface
                # atualizar_status(f"Erro ao abrir o arquivo: {e}", "error")
                print(f"Erro ao abrir o arquivo: {e}")
        else:
            # TODO: Implementar envio de erro para interface
            # atualizar_status("Nenhum arquivo disponível para abrir.", "warning")
            print("Nenhum arquivo disponível para abrir.")