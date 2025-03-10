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
from tkinter import Tk, ttk, filedialog, messagebox, Canvas
import tkinter as tk
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import threading
import json
import time
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

# Função para encontrar o caminho do recurso em desenvolvimento ou no executável
def resource_path(relative_path):
    """Obter o caminho absoluto para o recurso, funcionando para dev e para PyInstaller"""
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class SplashScreen:
    def __init__(self, parent):
        self.parent = parent
        self.splash = tk.Toplevel(parent)
        self.splash.title("Carregando...")
        self.splash.overrideredirect(True)  # Remove bordas da janela
        
        # Configurar a janela para ficar no topo
        self.splash.attributes("-topmost", True)
        
        # Carregar a imagem de splash
        try:
            # Usar resource_path para encontrar o caminho correto da imagem
            splash_image_path = resource_path("splashLogo.png")
            splash_image = Image.open(splash_image_path)
            # Obter dimensões da imagem
            width, height = splash_image.size
            
            # Configurar a geometria da janela
            screen_width = self.splash.winfo_screenwidth()
            screen_height = self.splash.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.splash.geometry(f"{width}x{height}+{x}+{y}")
            
            # Criar um canvas com fundo transparente
            self.canvas = Canvas(self.splash, width=width, height=height, 
                                bg='#f0f0f0', highlightthickness=0)
            self.canvas.pack()
            
            # Converter a imagem para formato Tkinter
            self.tk_image = ImageTk.PhotoImage(splash_image)
            
            # Adicionar a imagem ao canvas
            self.canvas.create_image(width//2, height//2, image=self.tk_image)
            
            # Adicionar texto de versão
            self.canvas.create_text(width//2, height-20, 
                                   text=f"Versão {APP_VERSION}", 
                                   fill="#333333", font=("Segoe UI", 10))
            
            # Adicionar barra de progresso
            self.progress_var = tk.DoubleVar()
            self.progress = ttk.Progressbar(self.splash, variable=self.progress_var, 
                                          length=width-40, mode="determinate")
            self.progress_window = self.canvas.create_window(width//2, height-40, 
                                                          window=self.progress)
            
            # Adicionar texto de status
            self.status_text = self.canvas.create_text(width//2, height-60, 
                                                    text="Inicializando...", 
                                                    fill="#333333", font=("Segoe UI", 9))
        except Exception as e:
            print(f"Erro ao carregar splash screen: {e}")
            self.splash.destroy()
    
    def update_progress(self, value, status_text):
        """Atualiza o progresso e o texto de status"""
        self.progress_var.set(value)
        self.canvas.itemconfig(self.status_text, text=status_text)
        self.splash.update_idletasks()
    
    def destroy(self):
        """Fecha a splash screen"""
        self.splash.destroy()

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
    # Criar janela principal (inicialmente oculta)
    root = ThemedTk(theme="azure")
    root.withdraw()  # Ocultar a janela principal durante o carregamento
    root.title(f"{APP_NAME} - v{APP_VERSION}")
    
    # Criar e mostrar a splash screen
    splash = SplashScreen(root)
    
    # Funções auxiliares que serão usadas na inicialização
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
            backup_path = Path("backups") / backup_filename
            
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
            for arquivo in Path("backups").glob("*"):
                if arquivo.is_file():
                    arquivo.unlink()
                    
            atualizar_status("Histórico e backups limpos com sucesso!", "success")
        except Exception as e:
            atualizar_status(f"Erro ao limpar histórico e backups: {e}", "error")
    
    def abrir_backup():
        """Abre a janela para selecionar e abrir um arquivo de backup"""
        try:
            # Verificar se existem backups
            backups = list(Path("backups").glob("*"))
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
        """Atualiza a mensagem de status na barra inferior"""
        if not status_label:
            print(mensagem)  # Fallback se a interface não estiver pronta
            return
            
        status_label.config(text=mensagem)
        if tipo == "error":
            status_label.config(foreground="red")
        elif tipo == "success":
            status_label.config(foreground="green")
        elif tipo == "warning":
            status_label.config(foreground="orange")
        else:
            status_label.config(foreground="black")
        root.update_idletasks()
        
    def mostrar_progresso(progresso):
        """Atualiza a barra de progresso"""
        if not progress_bar:
            return
            
        progress_bar["value"] = progresso
        root.update_idletasks()
        
    def adicionar_historico(operacao):
        """Adiciona uma operação ao histórico"""
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        historico_operacoes.append({
            "data": data_atual,
            "operacao": operacao
        })
        salvar_historico()
        atualizar_lista_historico()
        
    def atualizar_lista_historico():
        """Atualiza a lista de histórico na interface"""
        if not historico_list:
            return
            
        historico_list.delete(0, tk.END)
        for item in historico_operacoes:
            historico_list.insert(tk.END, f"{item['data']} - {item['operacao']}")
    
    def salvar_historico():
        """Salva o histórico de operações em um arquivo JSON"""
        try:
            with open("historico_operacoes.json", "w") as f:
                json.dump(historico_operacoes, f)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
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
        
    def sobre():
        """Mostra informações sobre o programa"""
        messagebox.showinfo(
            f"Sobre - {APP_NAME}",
            f"{APP_NAME}\nVersão {APP_VERSION}\n\nDesenvolvido por Arthur Morais\n© 2024 Todos os direitos reservados"
        )
    
    # Modificar a abordagem de inicialização para evitar problemas de threading com Tcl
    def inicializar_com_atraso():
        try:
            # Configurações de estilo
            splash.update_progress(10, "Configurando estilos...")
            style = ttk.Style()
            style.configure("Custom.TFrame", background="#f0f0f0")
            style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
            style.configure("Status.TLabel", font=("Segoe UI", 9), padding=5)
            style.configure("Custom.TButton", font=("Segoe UI", 9), padding=5)
            
            # Variáveis de controle
            nonlocal arquivo_salvo, historico_operacoes
            nonlocal status_label, progress_bar, historico_list, entry_bordero, combobox_carteira, gerar_botao, abrir_botao
            
            # Criar pasta de backups se não existir
            splash.update_progress(20, "Verificando diretórios...")
            backup_dir = Path("backups")
            if not backup_dir.exists():
                backup_dir.mkdir()
            
            # Carregar histórico
            splash.update_progress(30, "Carregando histórico...")
            historico_operacoes = carregar_historico()
            
            # Verificar atualizações
            splash.update_progress(40, "Verificando atualizações...")
            info_atualizacao = verificar_atualizacao()
            
            # Configurar a janela principal
            splash.update_progress(60, "Configurando interface...")
            centralizar_janela(root, 800, 600)
            
            try:
                root.iconbitmap(resource_path("favicon-b3.ico"))
            except Exception:
                pass
                
            # Criar interface completa
            splash.update_progress(80, "Construindo interface...")
            
            # Configuração da janela principal
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
            
            # Atualizar lista de histórico
            splash.update_progress(90, "Finalizando...")
            atualizar_lista_historico()
            
            # Finalizar inicialização
            splash.update_progress(100, "Pronto!")
            time.sleep(0.5)  # Pequena pausa para mostrar 100%
            
            # Mostrar a janela principal e destruir a splash
            root.deiconify()  # Mostrar a janela principal
            splash.destroy()  # Fechar a splash screen
            
            # Verificar atualizações em segundo plano
            if info_atualizacao['disponivel']:
                # Usar after para agendar na thread principal
                root.after(1000, lambda: mostrar_atualizacao_disponivel(info_atualizacao))
        except Exception as e:
            print(f"Erro durante a inicialização: {e}")
            # Garantir que a splash screen seja fechada mesmo em caso de erro
            try:
                splash.destroy()
            except:
                pass
            root.deiconify()  # Tentar mostrar a janela principal mesmo em caso de erro
    
    # Variáveis globais para o escopo da interface
    arquivo_salvo = [None]
    historico_operacoes = []
    
    # Definir variáveis para componentes de interface que serão acessados por funções
    status_label = None
    progress_bar = None
    historico_list = None
    entry_bordero = None
    combobox_carteira = None
    gerar_botao = None
    abrir_botao = None
    
    # Funções para atualizar a interface
    def atualizar_status(mensagem, tipo="info"):
        """Atualiza a mensagem de status na barra inferior"""
        if not status_label:
            print(mensagem)  # Fallback se a interface não estiver pronta
            return
            
        status_label.config(text=mensagem)
        if tipo == "error":
            status_label.config(foreground="red")
        elif tipo == "success":
            status_label.config(foreground="green")
        elif tipo == "warning":
            status_label.config(foreground="orange")
        else:
            status_label.config(foreground="black")
        root.update_idletasks()
        
    def mostrar_progresso(progresso):
        """Atualiza a barra de progresso"""
        if not progress_bar:
            return
            
        progress_bar["value"] = progresso
        root.update_idletasks()
        
    def adicionar_historico(operacao):
        """Adiciona uma operação ao histórico"""
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        historico_operacoes.append({
            "data": data_atual,
            "operacao": operacao
        })
        salvar_historico()
        atualizar_lista_historico()
        
    def atualizar_lista_historico():
        """Atualiza a lista de histórico na interface"""
        if not historico_list:
            return
            
        historico_list.delete(0, tk.END)
        for item in historico_operacoes:
            historico_list.insert(tk.END, f"{item['data']} - {item['operacao']}")
    
    # Iniciar a inicialização na thread principal usando after
    root.after(100, inicializar_com_atraso)
    
    # Loop principal
    root.mainloop()

if __name__ == "__main__":
    interface()