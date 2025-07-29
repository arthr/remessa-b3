# app.py
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

# Adicionar o diretório src ao sys.path para permitir importações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Settings
from src.database.connection import DatabaseConnection
from src.ui import SplashScreen
from src.ui.dialogs import UpdateAvailableDialog
from src.services import (
    HistoryService, FileService, BackupService, BorderoService, UpdateService
)

from src.utils import (
    validar_bordero,
    resource_path,
    remover_acentos,
    verificar_configuracoes_banco,
    centralizar_janela
)

# Carregar configurações
settings = Settings()

# Informações da versão e configurações
APP_VERSION = settings.app_version
APP_NAME = settings.app_name
GITHUB_REPO = settings.github_repo
GITHUB_API_URL = settings.github_api_url
GITHUB_TOKEN = settings.github_token

# Configurações do banco de dados
DB_SERVER = settings.db_server
DB_NAME = settings.db_name
DB_USER = settings.db_user
DB_PASSWORD = settings.db_password

# Configurações de carteira
CARTEIRA_FIDC_ID = settings.carteira_fidc_id
CARTEIRA_PROPRIA_ID = settings.carteira_propria_id

# Configurações de layout B3
CONTA_ESCRITURADOR = settings.conta_escriturador
CNPJ_TITULAR = settings.cnpj_titular
RAZAO_TITULAR = settings.razao_titular

# Main Window
def interface():
    # Criar janela principal (inicialmente oculta)
    root = ThemedTk(theme="azure")
    root.withdraw()  # Ocultar a janela principal durante o carregamento
    root.title(f"{APP_NAME} - v{APP_VERSION}")
    
    # Criar e mostrar a splash screen
    splash = SplashScreen(root)
    
    # Funções auxiliares que serão usadas na inicialização
    history_service = HistoryService()
    file_service = FileService()
    backup_service = BackupService()
    update_service = UpdateService()
    
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
            history_service.limpar_historico()
            history_service.salvar_historico()

            atualizar_lista_historico()
            
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
                # Atualizar para usar o novo formato de nome do arquivo de backup (sem prefixo bordero_)
                nome_arquivo = backup.name
                match = re.search(r'(\d+)_', nome_arquivo)
                bordero_num = match.group(1) if match else "N/A"
                
                # Adicionar à lista
                backup_listbox.insert(tk.END, f"Borderô: {bordero_num} Data: {mod_time_str} Arquivo: {nome_arquivo}")
            
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
                    history_service.adicionar_historico(f"Arquivo de backup aberto: {arquivo_backup.name}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {e}")
            
            # Botões
            ttk.Button(button_frame, text="Abrir", command=abrir_arquivo_selecionado).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancelar", command=backup_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Duplo clique para abrir
            backup_listbox.bind("<Double-1>", lambda e: abrir_arquivo_selecionado())
            
        except Exception as e:
            atualizar_status(f"Erro ao abrir janela de backups: {e}", "error")
    
    # Função usada pela interface para atualizar a mensagem de status
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

    # Função usada pela interface para atualizar a barra de progresso
    def mostrar_progresso(progresso):
        """Atualiza a barra de progresso"""
        if not progress_bar:
            return
            
        progress_bar["value"] = progresso
        root.update_idletasks()

    # Função usada pela interface para atualizar a lista de histórico
    def atualizar_lista_historico():
        """Atualiza a lista de histórico na interface"""
        if not historico_list:
            return
            
        historico_list.delete(0, tk.END)
        for item in history_service.historico_operacoes:
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

            # Conecta ao banco de dados e executa a consulta
            # Atualiza o status e a barra de progresso da interface
            try:
                atualizar_status("Conectando ao banco de dados...", "info")
                mostrar_progresso(20)

                atualizar_status("Executando consulta...", "info")
                mostrar_progresso(40)

                # Executa a consulta
                dados = BorderoService().consultar_bordero(bordero, carteira_id)
                
                if not dados:
                    atualizar_status("Erro: Nenhum dado retornado para o Borderô.", "error")
                    return

                # Salvar dados da consulta para uso posterior
                dados_ultima_consulta[0] = dados

                # Calcular resumo da situação dos títulos
                total_titulos = len(dados)
                titulos_pagos = sum(1 for d in dados if d.get('Situacao') == 'PAGO')
                titulos_abertos = total_titulos - titulos_pagos
                
                # Mostrar resumo da situação
                resumo_situacao = f"Total: {total_titulos} | PAGOS: {titulos_pagos} | EM ABERTO: {titulos_abertos}"
                atualizar_status(f"Consulta concluída - {resumo_situacao}", "info")

                mostrar_progresso(60)
                
                # Selecionar nome do arquivo para salvar
                atualizar_status("Selecionando arquivo para salvar...", "info")
                mostrar_progresso(70)
                
                arquivo_nome = filedialog.asksaveasfilename(
                    title="Salvar Arquivo de Posições",
                    defaultextension=".txt",
                    filetypes=[("Arquivos de Texto", "*.txt")]
                )

                # Se o usuário cancelou a seleção do arquivo, cancela a geração
                if not arquivo_nome:
                    atualizar_status("Geração cancelada pelo usuário.", "info")
                    return

                # Se o usuário selecionou um arquivo, continua a geração
                if arquivo_nome:
                    atualizar_status("Gerando arquivo, aguarde...", "info")
                    mostrar_progresso(80)

                    # Gera o arquivo remessa de posições
                    file_service.gerar_arquivo(dados, arquivo_nome)
                    arquivo_salvo[0] = arquivo_nome
                    
                    # Criar backup do arquivo
                    backup_path = backup_service.criar_backup(arquivo_nome, bordero)
                    
                    # Reabilita o botão de geração
                    abrir_botao.config(state="normal")

                    # Atualiza a barra de progresso e a mensagem de status
                    mostrar_progresso(100)
                    atualizar_status("Arquivo gerado com sucesso!", "success")
                    
                    # Adicionar ao histórico com informação do backup
                    info_backup = f" (Backup: {os.path.basename(backup_path)})" if backup_path else ""
                    history_service.adicionar_historico(f"Arquivo gerado: {arquivo_nome} (Borderô: {bordero}){info_backup}")
                
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
    
    def mostrar_detalhes_situacao(dados):
        """Mostra uma janela com detalhes da situação de cada título"""
        if not dados:
            messagebox.showinfo("Informação", "Nenhum dado disponível para mostrar.")
            return
            
        # Criar janela de detalhes
        detalhes_window = tk.Toplevel(root)
        detalhes_window.title("Detalhes da Situação dos Títulos")
        detalhes_window.geometry("800x600")
        detalhes_window.transient(root)
        detalhes_window.grab_set()
        
        # Centralizar a janela
        centralizar_janela(detalhes_window, 800, 600)
        
        # Frame principal
        main_frame = ttk.Frame(detalhes_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Detalhes da Situação dos Títulos", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Resumo
        total_titulos = len(dados)
        titulos_pagos = sum(1 for d in dados if d.get('Situacao') == 'PAGO')
        titulos_abertos = total_titulos - titulos_pagos
        
        resumo_frame = ttk.LabelFrame(main_frame, text="Resumo", padding=10)
        resumo_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(resumo_frame, text=f"Total de Títulos: {total_titulos}", 
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(resumo_frame, text=f"Títulos PAGOS: {titulos_pagos}", 
                 foreground="green", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(resumo_frame, text=f"Títulos EM ABERTO: {titulos_abertos}", 
                 foreground="orange", font=("Segoe UI", 10)).pack(anchor="w")
        
        # Frame para a lista com scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview para mostrar os dados
        columns = ('Título', 'Devedor', 'Valor', 'Vencimento', 'Situação')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        
        # Configurar colunas
        tree.heading('Título', text='Número do Título')
        tree.heading('Devedor', text='Devedor')
        tree.heading('Valor', text='Valor Face')
        tree.heading('Vencimento', text='Data Vencimento')
        tree.heading('Situação', text='Situação')
        
        tree.column('Título', width=120)
        tree.column('Devedor', width=200)
        tree.column('Valor', width=100)
        tree.column('Vencimento', width=100)
        tree.column('Situação', width=100)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        # Preencher dados
        for item in dados:
            situacao = item.get('Situacao', 'N/A')
            valor = item.get('Valor_Face', 0)
            vencimento = item.get('Data_Vencimento', '')
            
            # Formatar valor
            try:
                valor_formatado = f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                valor_formatado = str(valor)
            
            # Formatar vencimento
            if vencimento and len(vencimento) == 8:
                vencimento_formatado = f"{vencimento[:4]}-{vencimento[4:6]}-{vencimento[6:8]}"
            else:
                vencimento_formatado = vencimento
            
            # Definir cor baseada na situação
            tags = ('pago',) if situacao == 'PAGO' else ('aberto',)
            
            tree.insert('', tk.END, values=(
                item.get('Numero_Titulo', ''),
                item.get('Razao_Devedor', ''),
                valor_formatado,
                vencimento_formatado,
                situacao
            ), tags=tags)
        
        # Configurar cores
        tree.tag_configure('pago', foreground='green')
        tree.tag_configure('aberto', foreground='orange')
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Fechar", command=detalhes_window.destroy).pack(side=tk.RIGHT, padx=5)

    # Mostra informações sobre o programa
    # TODO: Migrar para UI/Dialogs
    def sobre():
        """Mostra informações sobre o programa"""
        messagebox.showinfo(
            f"Sobre - {settings.app_name}",
            f"{settings.app_name}\nVersão {settings.app_version}\n\nDesenvolvido por Arthur Morais\n© {datetime.now().year} Todos os direitos reservados\n"
        )
    
    # Mostra as configurações carregadas (para debug)
    # TODO: Migrar para UI/Dialogs
    def mostrar_configuracoes():
        """Mostra as configurações carregadas (para debug)"""
        config_ok, config_msg = verificar_configuracoes_banco(settings)
        
        info = f"Status das Configurações:\n{config_msg}\n\n"
        info += f"DB_SERVER: {'✓' if settings.db_server else '✗'} {settings.db_server or 'Não configurado'}\n"
        info += f"DB_NAME: {'✓' if settings.db_name else '✗'} {settings.db_name or 'Não configurado'}\n"
        info += f"DB_USER: {'✓' if settings.db_user else '✗'} {settings.db_user or 'Não configurado'}\n"
        info += f"DB_PASSWORD: {'✓' if settings.db_password else '✗'} {'***' if settings.db_password else 'Não configurado'}\n\n"
        info += f"Executável: {'Sim' if getattr(sys, 'frozen', False) else 'Não'}\n"
        info += f"Diretório atual: {os.getcwd()}"
        
        messagebox.showinfo("Configurações", info)
    
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
            nonlocal arquivo_salvo, dados_ultima_consulta
            nonlocal status_label, progress_bar, historico_list, entry_bordero, combobox_carteira, gerar_botao, abrir_botao
            
            # Criar pasta de backups se não existir
            splash.update_progress(20, "Verificando diretórios...")
            backup_dir = Path("backups")
            if not backup_dir.exists():
                backup_dir.mkdir()
            
            # Carregar histórico
            splash.update_progress(30, "Carregando histórico...")
            history_service.carregar_historico()
            
            # Verificar atualizações
            splash.update_progress(40, "Verificando atualizações...")
            update_service.check_for_updates()
            info_atualizacao = update_service.get_update_info()
            
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
            arquivo_menu.add_command(label="Abrir Último Arquivo", command=file_service.abrir_arquivo)
            arquivo_menu.add_command(label="Abrir Arquivo de Backup", command=abrir_backup)
            arquivo_menu.add_separator()
            arquivo_menu.add_command(label="Ver Detalhes da Situação", command=lambda: mostrar_detalhes_situacao(dados_ultima_consulta[0]) if dados_ultima_consulta[0] else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."))
            arquivo_menu.add_separator()
            arquivo_menu.add_command(label="Limpar Histórico e Backups", command=limpar_historico_e_backups)
            arquivo_menu.add_separator()
            arquivo_menu.add_command(label="Sair", command=root.quit)
            
            ajuda_menu = tk.Menu(menu_bar, tearoff=0)
            menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
            ajuda_menu.add_command(label="Verificar Atualizações", command=lambda: threading.Thread(target=lambda: UpdateAvailableDialog(root, update_service) if update_service.get_update_info()['disponivel'] else messagebox.showinfo("Atualização", "Você já está usando a versão mais recente."), daemon=True).start())
            ajuda_menu.add_command(label="Ver Configurações", command=mostrar_configuracoes)
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
            
            abrir_botao = ttk.Button(button_frame, text="Abrir Arquivo", command=file_service.abrir_arquivo, 
                                state="disabled", style="Custom.TButton")
            abrir_botao.pack(side=tk.LEFT, padx=5)
            
            backup_botao = ttk.Button(button_frame, text="Abrir Backup", command=abrir_backup, style="Custom.TButton")
            backup_botao.pack(side=tk.LEFT, padx=5)
            
            detalhes_botao = ttk.Button(button_frame, text="Ver Detalhes", command=lambda: mostrar_detalhes_situacao(dados_ultima_consulta[0]) if dados_ultima_consulta[0] else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."), style="Custom.TButton")
            detalhes_botao.pack(side=tk.LEFT, padx=5)
            
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
                root.after(1000, lambda: UpdateAvailableDialog(root, update_service))
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
    dados_ultima_consulta = [None]  # Armazena os dados da última consulta
    
    # Definir variáveis para componentes de interface que serão acessados por funções
    status_label = None
    progress_bar = None
    historico_list = None
    entry_bordero = None
    combobox_carteira = None
    gerar_botao = None
    abrir_botao = None
    
    # Funções usadas pela interface para atualizar a mensagem de status
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
        
    # Função usada pela interface para atualizar a barra de progresso
    def mostrar_progresso(progresso):
        """Atualiza a barra de progresso"""
        if not progress_bar:
            return
            
        progress_bar["value"] = progresso
        root.update_idletasks()
        """Atualiza a lista de histórico na interface"""
        if not historico_list:
            return
            
        historico_list.delete(0, tk.END)
        for item in history_service.historico_operacoes:
            historico_list.insert(tk.END, f"{item['data']} - {item['operacao']}")
    
    # Iniciar a inicialização na thread principal usando after
    root.after(100, inicializar_com_atraso)
    
    # Loop principal
    root.mainloop()

if __name__ == "__main__":
    interface()