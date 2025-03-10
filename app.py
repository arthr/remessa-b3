import subprocess
import re
import pyodbc
import os
import sys
import unicodedata
import shutil
import requests
import webbrowser
from packaging import version
from datetime import datetime
from tkinter import Tk, ttk, filedialog, messagebox
import tkinter as tk
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import threading
import json
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Informações da versão e configurações
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")
APP_NAME = os.getenv("APP_NAME", "Remessa B3")
GITHUB_REPO = os.getenv("GITHUB_REPO", "arthr/remessa-b3")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Configurações do banco de dados
DB_SERVER = os.getenv("DB_SERVER", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Configurações de carteira
CARTEIRA_FIDC_ID = int(os.getenv("CARTEIRA_FIDC_ID", "2"))
CARTEIRA_PROPRIA_ID = int(os.getenv("CARTEIRA_PROPRIA_ID", "0"))

# Configurações de layout B3
CONTA_ESCRITURADOR = os.getenv("CONTA_ESCRITURADOR", "58561405")
CNPJ_TITULAR = os.getenv("CNPJ_TITULAR", "51030944000142")
RAZAO_TITULAR = os.getenv("RAZAO_TITULAR", "DIRETA CAPITAL FIDC")

def remover_acentos(texto):
    normalizado = unicodedata.normalize("NFD", texto)
    return ''.join(char for char in normalizado if unicodedata.category(char) != 'Mn')

def conectar_banco(server=None, database=None, user=None, password=None):
    """Conecta ao banco de dados usando as credenciais fornecidas ou as variáveis de ambiente"""
    try:
        server = server or DB_SERVER
        database = database or DB_NAME
        user = user or DB_USER
        password = password or DB_PASSWORD
        
        if not all([server, database, user, password]):
            raise ValueError("Credenciais de banco de dados incompletas")
            
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={user};PWD={password}"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
        return None

def executar_query(conn, bordero, carteira_id=None):
    query = """
    -- Coloque aqui a query que você forneceu
    WITH Titulos_Dor AS (
        SELECT 
            '1' AS Tipo_Registro,
            'INCL' AS Inclusao,
            tit.[ctrl_id] AS Id,
            tit.Carteira_ID,
            cart.Nome AS Carteira,
            'DIRETA CAPITAL FIDC' AS Razao_Titular,
            '51030944000142' AS CNPJ_Titular,
            '' AS Conta_do_Titular,
            '' AS Meu_Numero,
            '' AS Manutencao,
            '2' AS Tipo_Regime,
            ced.CGC AS CNPJ_Credor,
            UPPER(ced.NOME) AS Razao_Credor,
            ced.ESTADO AS UF,
            UPPER(ced.CIDADE) AS CIDADE,
            sac.CGC AS CNPJ_Devedor,
            UPPER(sac.NOME) AS Razao_Devedor,
            'Boleto' AS Pagamento,
            'DC' AS Tipo_IF,
            'INCL' AS Acao,
            '' AS Codigo_IF,
            '' AS Vencimento_Atualizada,
            '58561405' AS Conta_Escriturador,
            '' AS Data_Valor_Atualizado,
            CASE tit.tipodcto
                WHEN 'DM' THEN '02'
                WHEN 'DS' THEN '05'
                ELSE 'XX'
            END AS Especie_Titulo,
            tit.[BORDERO] AS Numero_Bordero,
            tit.[DCTO] AS Numero_Titulo,
            CONVERT(VARCHAR(8), tit.[DTBORDERO], 112) AS Data_Operacao,
            CONVERT(VARCHAR(8), tit.[DATA], 112) AS Data_Vencimento,
            CAST(tit.[VALOR] AS DECIMAL(18,2)) AS Valor_Face,
            CAST(tit.[VALOR] AS DECIMAL(18,2)) AS Valor_Atualizado,
            td.descricao AS Tipo_Documento,
            CAST(tit.ValorNota AS DECIMAL(18,2)) AS Valor_nota_fiscal,
            tit.BORDERO AS Bordero,
            COALESCE(sflu.BANCO, sfidc.BANCO) AS Banco
        FROM 
            [wba].[dbo].[SIGFLS] tit
        JOIN 
            [wba].[dbo].[SIGBORS] bor ON tit.BORDERO = bor.BORDERO
        JOIN 
            [wba].[dbo].[tipodcto] td ON tit.tipodcto = td.tipodcto
        LEFT JOIN 
            [wba].[dbo].[SIGCAD] ced ON tit.CLIFOR = ced.CODIGO
        LEFT JOIN 
            [wba].[dbo].[SIGCAD] sac ON tit.SACADO = sac.CODIGO
        JOIN 
            [wba].[dbo].[Carteira] cart ON cart.NumeroCarteira = tit.Carteira_ID
        LEFT JOIN 
            [wba].[dbo].[SIGFLU] sflu ON tit.ctrl_id = sflu.sigfls
        LEFT JOIN 
            [wba].[dbo].[SIGFIDC] sfidc ON tit.ctrl_id = sfidc.sigfls
        WHERE 
            1=1
            AND (COALESCE(sflu.BANCO, sfidc.BANCO) IS NULL OR COALESCE(sflu.BANCO, sfidc.BANCO) = '  ' OR COALESCE(sflu.BANCO, sfidc.BANCO) = '')
            AND (tit.rejeitado NOT IN ('X', 'S') OR tit.rejeitado IS NULL)
            AND bor.dtliberacao IS NOT NULL
            AND td.tipodcto IN ('DM', 'DS')
    ),
    Titulos_Nfe AS (
        SELECT
            a.numero,
            a.serie,
            CONVERT(VARCHAR(8), a.Data_Emissao, 112) AS Data_Emissao,
            CAST(a.valor AS DECIMAL(18,2)) AS valor,
            a.chave,
            a.Ctrl_ID
        FROM
            [wba].[dbo].[nfeimportada] a
        INNER JOIN 
            [wba].[dbo].[nfeimportadaxsigfls] b ON b.nfeimportada_id = a.ctrl_id
    
        UNION ALL
    
        SELECT
            a.numero,
            a.serie,
            CONVERT(VARCHAR(8), a.Data_Emissao, 112) AS Data_Emissao,
            CAST(a.valor AS DECIMAL(18,2)) AS valor,
            a.chave,
            a.Ctrl_ID
        FROM
            [wba].[dbo].[nfeimportada] a
        INNER JOIN 
            [wba].[dbo].[NFeImportadaXSigflsMultiplasNFes] b ON b.NFeImportada_ID = a.Ctrl_ID
    )
    
    SELECT 
        Id,
        Carteira_ID,
        Tipo_IF,
        Tipo_Registro,
        Acao,
        Codigo_IF,
        Conta_Escriturador,
        Conta_do_Titular,
        CNPJ_Titular,
        Razao_Titular,
        Meu_Numero,
        Manutencao,
        Tipo_Regime,
        CNPJ_Credor,
        Razao_Credor,
        CNPJ_Devedor,
        Razao_Devedor,
        Valor_Face,
        Valor_Atualizado,
        Data_Valor_Atualizado,
        ISNULL(Data_Emissao, Data_Operacao) AS Data_Emissao,
        Data_Vencimento,
        Vencimento_Atualizada,
        UF,
        CIDADE,
        Especie_Titulo,
        Valor_nota_fiscal,
        Data_Operacao,
        Numero_Bordero,
        Pagamento,
        ISNULL(Numero_Titulo, '') Numero_Titulo,
        ISNULL(Chave, '') Chave,
        Bordero,
        ISNULL(Numero, '') Numero,
        ISNULL(Serie, '') Serie,
        Tipo_Documento,
        Carteira,
        ISNULL(Banco, '') Banco
    FROM 
        Titulos_Dor
    LEFT JOIN 
        Titulos_Nfe
    ON Ctrl_ID = Id

    WHERE 1=1
    AND Bordero = ?
    {carteira_filtro}
    """.format(
            carteira_filtro="" if carteira_id is None else "AND Carteira_ID = ?"
        ) + """
    ORDER BY 
        Data_Operacao DESC
    """
    try:
        cursor = conn.cursor()
        if carteira_id is not None:
            cursor.execute(query, (bordero, carteira_id))
        else:
            cursor.execute(query, (bordero,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        messagebox.showerror("Erro na Query", f"Ocorreu um erro ao executar a query: {e}")
        return []

def gerar_header():
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

def gerar_arquivo(dados, output_file):
    try:
        with open(output_file, "w") as f:
            f.write(gerar_header() + "\n")
            for row in dados:
                linha = (
                    f"{row.get('Tipo_IF').ljust(5)}"  # Tipo IF
                    f"{row.get('Tipo_Registro', '1').ljust(1)}"  # Tipo de Registro
                    f"{row.get('Acao', 'INCL').ljust(4)}"  # Ação
                    f"{(row.get('Codigo_IF') or '').rjust(14)}"  # Código IF
                    f"{(row.get('Conta_Escriturador', CONTA_ESCRITURADOR) or CONTA_ESCRITURADOR).rjust(8)}"  # Conta Escriturador
                    f"{(row.get('Conta_do_Titular', '') or '').rjust(8)}"  # Conta do Titular
                    f"{re.sub(r'\D', '', (row.get('CNPJ_Titular', CNPJ_TITULAR) or CNPJ_TITULAR)).rjust(14)}"  # CPF/CNPJ do Titular
                    f"{remover_acentos(row.get('Razao_Titular', RAZAO_TITULAR) or RAZAO_TITULAR).ljust(100)}"  # Razão Social do Titular
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
                    f"{'02'.rjust(2)}"  # Status do Pagamento (01 - Pago, 02 - Em Aberto. Na ação INCL deve ser sempre 02)
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
        messagebox.showerror("Erro na Exportação", f"Erro ao gerar o arquivo: {e}")

def validar_bordero(bordero):
    if not bordero.isdigit():
        messagebox.showerror("Erro", "O número do Borderô deve conter apenas dígitos!")
        return False
    return True

def centralizar_janela(root, largura=500, altura=300):
    """Centraliza a janela na tela."""
    # Pega a largura e altura da tela
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()

    # Calcula as coordenadas para centralizar
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)

    # Define a geometria da janela
    root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

def verificar_atualizacao():
    """Verifica se há uma nova versão disponível no GitHub"""
    try:
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            ultima_versao = dados.get('tag_name', '').lstrip('v')
            
            if version.parse(ultima_versao) > version.parse(APP_VERSION):
                return {
                    'disponivel': True,
                    'versao': ultima_versao,
                    'url': dados.get('html_url', ''),
                    'notas': dados.get('body', 'Notas de lançamento não disponíveis.')
                }
        
        return {'disponivel': False}
    except Exception:
        return {'disponivel': False}

def interface():
    # Configuração do tema e estilo
    root = ThemedTk(theme="azure")
    root.title(f"{APP_NAME} - v{APP_VERSION}")
    
    # Configurações de estilo
    style = ttk.Style()
    style.configure("Custom.TFrame", background="#f0f0f0")
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
    style.configure("Status.TLabel", font=("Segoe UI", 9), padding=5)
    style.configure("Custom.TButton", font=("Segoe UI", 9), padding=5)
    
    # Variáveis de controle
    arquivo_salvo = [None]
    historico_operacoes = []
    
    # Criar pasta de backups se não existir
    backup_dir = Path("backups")
    if not backup_dir.exists():
        backup_dir.mkdir()
    
    def salvar_historico():
        """Salva o histórico de operações em um arquivo JSON"""
        try:
            with open("historico_operacoes.json", "w") as f:
                json.dump(historico_operacoes, f)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def carregar_historico():
        """Carrega o histórico de operações do arquivo JSON"""
        try:
            if Path("historico_operacoes.json").exists():
                with open("historico_operacoes.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
        return []
    
    def fazer_backup_arquivo(arquivo_original, bordero):
        """Cria uma cópia do arquivo gerado na pasta de backups"""
        try:
            if not arquivo_original:
                return None
                
            # Garantir que o nome do arquivo seja seguro para o sistema de arquivos
            bordero_seguro = re.sub(r'[^\w\-_]', '_', bordero)
            
            # Obter a extensão do arquivo original
            _, ext = os.path.splitext(arquivo_original)
            
            # Criar nome do arquivo de backup com timestamp para evitar sobrescrever
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"bordero_{bordero_seguro}_{timestamp}{ext}"
            backup_path = backup_dir / backup_filename
            
            # Copiar o arquivo
            shutil.copy2(arquivo_original, backup_path)
            
            return str(backup_path)
        except Exception as e:
            atualizar_status(f"Erro ao criar backup: {e}", "error")
            return None
    
    def limpar_historico_e_backups():
        """Limpa o histórico de operações e os arquivos de backup"""
        try:
            # Confirmar com o usuário
            resposta = messagebox.askyesno(
                "Confirmar Exclusão", 
                "Isso excluirá todo o histórico de operações e todos os arquivos de backup. Continuar?"
            )
            
            if not resposta:
                return
                
            # Limpar histórico
            historico_operacoes.clear()
            atualizar_lista_historico()
            salvar_historico()
            
            # Limpar arquivos de backup
            for arquivo in backup_dir.glob("*"):
                if arquivo.is_file():
                    arquivo.unlink()
                    
            atualizar_status("Histórico e backups limpos com sucesso!", "success")
        except Exception as e:
            atualizar_status(f"Erro ao limpar histórico e backups: {e}", "error")
    
    def abrir_backup():
        """Abre a janela para selecionar e abrir um arquivo de backup"""
        try:
            # Verificar se existem backups
            backups = list(backup_dir.glob("*"))
            if not backups:
                messagebox.showinfo("Informação", "Não há arquivos de backup disponíveis.")
                return
                
            # Criar janela de seleção
            backup_window = tk.Toplevel(root)
            backup_window.title("Selecionar Arquivo de Backup")
            backup_window.geometry("600x400")
            backup_window.transient(root)
            backup_window.grab_set()
            
            # Centralizar a janela
            centralizar_janela(backup_window, 600, 400)
            
            # Frame principal
            main_frame = ttk.Frame(backup_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Label de instrução
            ttk.Label(main_frame, text="Selecione um arquivo de backup para abrir:", 
                     font=("Segoe UI", 10)).pack(pady=5, anchor="w")
            
            # Frame para a lista com scrollbar
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Lista de backups
            backup_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 9))
            backup_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=backup_listbox.yview)
            
            # Preencher a lista com os arquivos de backup (mais recentes primeiro)
            backups_sorted = sorted(backups, key=os.path.getmtime, reverse=True)
            for backup in backups_sorted:
                # Formatar a data de modificação
                mod_time = datetime.fromtimestamp(os.path.getmtime(backup))
                mod_time_str = mod_time.strftime("%d/%m/%Y %H:%M:%S")
                
                # Extrair o número do borderô do nome do arquivo
                nome_arquivo = backup.name
                match = re.search(r'bordero_(\w+)_', nome_arquivo)
                bordero_num = match.group(1) if match else "N/A"
                
                # Adicionar à lista
                backup_listbox.insert(tk.END, f"Borderô: {bordero_num} - {mod_time_str} - {nome_arquivo}")
            
            # Frame para botões
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            # Função para abrir o arquivo selecionado
            def abrir_arquivo_selecionado():
                selecionado = backup_listbox.curselection()
                if not selecionado:
                    messagebox.showinfo("Informação", "Selecione um arquivo para abrir.")
                    return
                    
                # Obter o arquivo selecionado
                arquivo_backup = backups_sorted[selecionado[0]]
                
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(arquivo_backup)
                    elif os.name == 'posix':  # macOS ou Linux
                        subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', str(arquivo_backup)))
                    
                    backup_window.destroy()
                    adicionar_historico(f"Arquivo de backup aberto: {arquivo_backup.name}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {e}")
            
            # Botões
            ttk.Button(button_frame, text="Abrir", command=abrir_arquivo_selecionado).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancelar", command=backup_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Duplo clique para abrir
            backup_listbox.bind("<Double-1>", lambda e: abrir_arquivo_selecionado())
            
        except Exception as e:
            atualizar_status(f"Erro ao abrir janela de backups: {e}", "error")
    
    def atualizar_status(mensagem, tipo="info"):
        """Atualiza a barra de status com uma mensagem e cor apropriada"""
        cores = {
            "info": "#000000",
            "success": "#008000",
            "error": "#FF0000",
            "warning": "#FFA500"
        }
        status_label.config(text=mensagem, foreground=cores.get(tipo, "#000000"))
        root.update_idletasks()
    
    def mostrar_progresso(progresso):
        """Atualiza a barra de progresso"""
        progress_bar["value"] = progresso
        root.update_idletasks()
    
    def adicionar_historico(operacao):
        """Adiciona uma operação ao histórico"""
        historico_operacoes.insert(0, {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operacao": operacao
        })
        if len(historico_operacoes) > 100:  # Limita a 100 entradas
            historico_operacoes.pop()
        atualizar_lista_historico()
        salvar_historico()
    
    def atualizar_lista_historico():
        """Atualiza a lista de histórico na interface"""
        historico_list.delete(0, tk.END)
        for item in historico_operacoes:
            historico_list.insert(tk.END, f"{item['data']} - {item['operacao']}")
    
    def iniciar_geracao(event=None):
        """Inicia a geração do arquivo em uma thread separada"""
        def processo_geracao():
            bordero = entry_bordero.get()
            if not validar_bordero(bordero):
                atualizar_status("Erro: Número de Borderô inválido!", "error")
                return

            # Obter o ID da carteira selecionada
            carteira = combobox_carteira.get()
            carteira_id = None
            if carteira == "Carteira FIDC":
                carteira_id = CARTEIRA_FIDC_ID
            elif carteira == "Carteira Própria":
                carteira_id = CARTEIRA_PROPRIA_ID

            # Desabilitar controles durante o processamento
            entry_bordero.config(state="disabled")
            combobox_carteira.config(state="disabled")
            gerar_botao.config(state="disabled")

            try:
                # Conectar ao banco de dados
                atualizar_status("Conectando ao banco de dados...", "info")
                mostrar_progresso(20)
                conn = conectar_banco()
                if not conn:
                    atualizar_status("Erro: Não foi possível conectar ao banco.", "error")
                    return

                # Executar a query
                atualizar_status("Executando consulta...", "info")
                mostrar_progresso(40)
                dados = executar_query(conn, bordero, carteira_id)
                if not dados:
                    atualizar_status("Erro: Nenhum dado retornado para o Borderô.", "error")
                    return

                mostrar_progresso(60)
                # Selecionar nome do arquivo para salvar
                arquivo_nome = filedialog.asksaveasfilename(
                    title="Salvar Arquivo de Posições",
                    defaultextension=".txt",
                    filetypes=[("Arquivos de Texto", "*.txt")]
                )

                if arquivo_nome:
                    atualizar_status("Gerando arquivo, aguarde...", "info")
                    mostrar_progresso(80)
                    gerar_arquivo(dados, arquivo_nome)
                    arquivo_salvo[0] = arquivo_nome
                    
                    # Criar backup do arquivo
                    backup_path = fazer_backup_arquivo(arquivo_nome, bordero)
                    
                    abrir_botao.config(state="normal")
                    mostrar_progresso(100)
                    atualizar_status("Arquivo gerado com sucesso!", "success")
                    
                    # Adicionar ao histórico com informação do backup
                    info_backup = f" (Backup: {os.path.basename(backup_path)})" if backup_path else ""
                    adicionar_historico(f"Arquivo gerado: {arquivo_nome} (Borderô: {bordero}){info_backup}")
                
            except Exception as e:
                atualizar_status(f"Erro: {str(e)}", "error")
            finally:
                # Reabilitar controles
                entry_bordero.config(state="normal")
                combobox_carteira.config(state="readonly")
                gerar_botao.config(state="normal")
                entry_bordero.focus()
                mostrar_progresso(0)

        # Iniciar processo em thread separada
        threading.Thread(target=processo_geracao, daemon=True).start()

    def abrir_arquivo():
        """Abre o arquivo gerado"""
        if arquivo_salvo[0]:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(arquivo_salvo[0])
                elif os.name == 'posix':  # macOS ou Linux
                    subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', arquivo_salvo[0]))
                adicionar_historico(f"Arquivo aberto: {arquivo_salvo[0]}")
            except Exception as e:
                atualizar_status(f"Erro ao abrir o arquivo: {e}", "error")
        else:
            atualizar_status("Nenhum arquivo disponível para abrir.", "warning")

    def mostrar_atualizacao_disponivel(info_atualizacao):
        """Mostra uma janela informando sobre a atualização disponível"""
        update_window = tk.Toplevel(root)
        update_window.title("Atualização Disponível")
        update_window.geometry("500x400")
        update_window.transient(root)
        update_window.grab_set()
        
        # Centralizar a janela
        centralizar_janela(update_window, 500, 400)
        
        # Frame principal
        main_frame = ttk.Frame(update_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Nova Versão Disponível!", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Informações da versão
        ttk.Label(main_frame, text=f"Versão atual: {APP_VERSION}").pack(anchor="w", pady=2)
        ttk.Label(main_frame, text=f"Nova versão: {info_atualizacao['versao']}").pack(anchor="w", pady=2)
        
        # Notas de lançamento
        ttk.Label(main_frame, text="Notas de lançamento:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
        
        # Frame para as notas com scrollbar
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(notes_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=10, yscrollcommand=scrollbar.set)
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)
        
        notes_text.insert(tk.END, info_atualizacao['notas'])
        notes_text.config(state=tk.DISABLED)
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def abrir_pagina_download():
            webbrowser.open(info_atualizacao['url'])
            update_window.destroy()
        
        ttk.Button(button_frame, text="Baixar Atualização", command=abrir_pagina_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Lembrar Depois", command=update_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def verificar_atualizacoes_background():
        """Verifica atualizações em segundo plano"""
        info_atualizacao = verificar_atualizacao()
        if info_atualizacao['disponivel']:
            root.after(1000, lambda: mostrar_atualizacao_disponivel(info_atualizacao))
    
    def sobre():
        """Mostra informações sobre o programa"""
        messagebox.showinfo(
            f"Sobre - {APP_NAME}",
            f"{APP_NAME}\nVersão {APP_VERSION}\n\nDesenvolvido por Arthur Morais\n© 2024 Todos os direitos reservados"
        )

    # Configuração da janela principal
    centralizar_janela(root, 800, 600)
    
    try:
        root.iconbitmap("favicon-b3.ico")
    except Exception:
        pass

    # Menu superior
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    arquivo_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=arquivo_menu)
    arquivo_menu.add_command(label="Gerar Novo Arquivo", command=iniciar_geracao)
    arquivo_menu.add_command(label="Abrir Último Arquivo", command=abrir_arquivo)
    arquivo_menu.add_command(label="Abrir Arquivo de Backup", command=abrir_backup)
    arquivo_menu.add_separator()
    arquivo_menu.add_command(label="Limpar Histórico e Backups", command=limpar_historico_e_backups)
    arquivo_menu.add_separator()
    arquivo_menu.add_command(label="Sair", command=root.quit)
    
    ajuda_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
    ajuda_menu.add_command(label="Verificar Atualizações", command=lambda: threading.Thread(target=lambda: mostrar_atualizacao_disponivel(verificar_atualizacao()) if verificar_atualizacao()['disponivel'] else messagebox.showinfo("Atualização", "Você já está usando a versão mais recente."), daemon=True).start())
    ajuda_menu.add_command(label="Sobre", command=sobre)

    # Frame principal
    main_frame = ttk.Frame(root, style="Custom.TFrame")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Área de entrada de dados
    input_frame = ttk.LabelFrame(main_frame, text="Dados de Entrada", padding=10)
    input_frame.pack(fill=tk.X, padx=5, pady=5)

    # Grid para campos de entrada
    ttk.Label(input_frame, text="Número do Borderô:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_bordero = ttk.Entry(input_frame, width=30)
    entry_bordero.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    entry_bordero.bind("<Return>", iniciar_geracao)

    ttk.Label(input_frame, text="Filtrar por Carteira:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    combobox_carteira = ttk.Combobox(input_frame, values=["Todas", "Carteira FIDC", "Carteira Própria"], 
                                    state="readonly", width=27)
    combobox_carteira.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    combobox_carteira.set("Todas")

    # Frame para botões
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, padx=5, pady=10)

    gerar_botao = ttk.Button(button_frame, text="Gerar Arquivo", command=iniciar_geracao, style="Custom.TButton")
    gerar_botao.pack(side=tk.LEFT, padx=5)

    abrir_botao = ttk.Button(button_frame, text="Abrir Arquivo", command=abrir_arquivo, 
                            state="disabled", style="Custom.TButton")
    abrir_botao.pack(side=tk.LEFT, padx=5)
    
    backup_botao = ttk.Button(button_frame, text="Abrir Backup", command=abrir_backup, style="Custom.TButton")
    backup_botao.pack(side=tk.LEFT, padx=5)

    # Barra de progresso
    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill=tk.X, padx=5, pady=5)
    
    progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=100)
    progress_bar.pack(fill=tk.X, padx=5)

    # Frame para histórico
    historico_frame = ttk.LabelFrame(main_frame, text="Histórico de Operações", padding=10)
    historico_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Lista de histórico com scrollbar
    historico_scroll = ttk.Scrollbar(historico_frame)
    historico_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    historico_list = tk.Listbox(historico_frame, yscrollcommand=historico_scroll.set, 
                               font=("Segoe UI", 9), height=8)
    historico_list.pack(fill=tk.BOTH, expand=True)
    historico_scroll.config(command=historico_list.yview)

    # Barra de status
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    status_label = ttk.Label(status_frame, text="Pronto para iniciar...", 
                            style="Status.TLabel", relief="sunken")
    status_label.pack(fill=tk.X, padx=5, pady=5)

    # Carregar histórico salvo
    historico_operacoes = carregar_historico()
    atualizar_lista_historico()

    # Verificar atualizações em segundo plano
    threading.Thread(target=verificar_atualizacoes_background, daemon=True).start()

    # Loop principal
    root.mainloop()

if __name__ == "__main__":
    interface()
