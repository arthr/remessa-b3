# src/ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
import threading
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import re
from ..services.bordero_service import BorderoService
from ..services.file_service import FileService
from ..services.backup_service import BackupService
from ..services.update_service import UpdateService
from ..services.history_service import HistoryService
from ..ui.ui_manager import UIManagerImpl
from ..ui.dialogs.update_available import UpdateAvailableDialog
from ..utils import centralizar_janela, validar_bordero
from ..config.settings import Settings

class MainWindow:
    def __init__(self, bordero_service: BorderoService, 
                 file_service: FileService, 
                 backup_service: BackupService,
                 update_service: UpdateService,
                 ui_manager: UIManagerImpl):
        self.bordero_service = bordero_service
        self.file_service = file_service
        self.backup_service = backup_service
        self.update_service = update_service
        self.ui_manager = ui_manager
        self.history_service = HistoryService()
        self.settings = Settings()
        
        # Variáveis de controle
        self.arquivo_salvo = None
        self.dados_ultima_consulta = None
        self.status_label = None
        self.progress_bar = None
        self.historico_list = None
        self.entry_bordero = None
        self.combobox_carteira = None
        self.gerar_botao = None
        self.abrir_botao = None
        
        # Controle de thread para file dialog
        self.solicitar_arquivo = False
        self.arquivo_selecionado = None
        
        self.root = ThemedTk(theme="azure")
        self.setup_ui()
        self.carregar_historico()
        
        # Iniciar polling para verificar solicitação de arquivo
        self.verificar_solicitacao_arquivo()
    
    def setup_ui(self):
        """Configura a interface principal"""
        self.root.title(f"{self.settings.app_name} - v{self.settings.app_version}")
        self.root.geometry("800x600")
        
        # Configurar estilos
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#f0f0f0")
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Status.TLabel", font=("Segoe UI", 9), padding=5)
        style.configure("Custom.TButton", font=("Segoe UI", 9), padding=5)
        
        # Centralizar janela
        centralizar_janela(self.root, 800, 600)
        
        # Configurar menu
        self.setup_menu()
        
        # Configurar interface principal
        self.setup_main_frame()
        
        # Configurar barra de status
        self.setup_status_bar()
    
    def setup_menu(self):
        """Configura o menu da aplicação"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Menu Arquivo
        arquivo_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Arquivo", menu=arquivo_menu)
        arquivo_menu.add_command(label="Gerar Novo Arquivo", command=self.iniciar_geracao)
        arquivo_menu.add_command(label="Abrir Último Arquivo", command=self.file_service.abrir_arquivo)
        arquivo_menu.add_command(label="Abrir Arquivo de Backup", command=self.abrir_backup)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Ver Detalhes da Situação", 
                               command=lambda: self.mostrar_detalhes_situacao(self.dados_ultima_consulta) if self.dados_ultima_consulta else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."))
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Limpar Histórico e Backups", command=self.limpar_historico_e_backups)
        arquivo_menu.add_separator()
        arquivo_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Ajuda
        ajuda_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
        ajuda_menu.add_command(label="Verificar Atualizações", 
                             command=lambda: threading.Thread(target=lambda: UpdateAvailableDialog(self.root, self.update_service) if self.update_service.check_for_updates().disponivel else messagebox.showinfo("Atualização", "Você já está usando a versão mais recente."), daemon=True).start())
        ajuda_menu.add_command(label="Ver Configurações", command=self.mostrar_configuracoes)
        ajuda_menu.add_command(label="Sobre", command=self.sobre)
    
    def setup_main_frame(self):
        """Configura o frame principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style="Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Área de entrada de dados
        input_frame = ttk.LabelFrame(main_frame, text="Dados de Entrada", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Grid para campos de entrada
        ttk.Label(input_frame, text="Número do Borderô:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_bordero = ttk.Entry(input_frame, width=30)
        self.entry_bordero.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_bordero.bind("<Return>", self.iniciar_geracao)
        
        ttk.Label(input_frame, text="Filtrar por Carteira:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combobox_carteira = ttk.Combobox(input_frame, values=["Todas", "Carteira FIDC", "Carteira Própria"], 
                                        state="readonly", width=27)
        self.combobox_carteira.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.combobox_carteira.set("Todas")
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.gerar_botao = ttk.Button(button_frame, text="Gerar Arquivo", command=self.iniciar_geracao, style="Custom.TButton")
        self.gerar_botao.pack(side=tk.LEFT, padx=5)
        
        self.abrir_botao = ttk.Button(button_frame, text="Abrir Arquivo", command=self.file_service.abrir_arquivo, 
                                state="disabled", style="Custom.TButton")
        self.abrir_botao.pack(side=tk.LEFT, padx=5)
        
        backup_botao = ttk.Button(button_frame, text="Abrir Backup", command=self.abrir_backup, style="Custom.TButton")
        backup_botao.pack(side=tk.LEFT, padx=5)
        
        detalhes_botao = ttk.Button(button_frame, text="Ver Detalhes", 
                                  command=lambda: self.mostrar_detalhes_situacao(self.dados_ultima_consulta) if self.dados_ultima_consulta else messagebox.showinfo("Informação", "Execute uma consulta primeiro para ver os detalhes."), 
                                  style="Custom.TButton")
        detalhes_botao.pack(side=tk.LEFT, padx=5)
        
        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=100)
        self.progress_bar.pack(fill=tk.X, padx=5)
        
        # Frame para histórico
        historico_frame = ttk.LabelFrame(main_frame, text="Histórico de Operações", padding=10)
        historico_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Lista de histórico com scrollbar
        historico_scroll = ttk.Scrollbar(historico_frame)
        historico_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.historico_list = tk.Listbox(historico_frame, yscrollcommand=historico_scroll.set, 
                                    font=("Segoe UI", 9), height=8)
        self.historico_list.pack(fill=tk.BOTH, expand=True)
        historico_scroll.config(command=self.historico_list.yview)
    
    def setup_status_bar(self):
        """Configura a barra de status"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Pronto para iniciar...", 
                                style="Status.TLabel", relief="sunken")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
    
    def carregar_historico(self):
        """Carrega o histórico de operações"""
        self.history_service.carregar_historico()
        self.atualizar_lista_historico()
    
    def atualizar_lista_historico(self):
        """Atualiza a lista de histórico na interface"""
        if not self.historico_list:
            return
            
        self.historico_list.delete(0, tk.END)
        for item in self.history_service.historico_operacoes:
            self.historico_list.insert(tk.END, f"{item['data']} - {item['operacao']}")
    
    def iniciar_geracao(self, event=None):
        """Inicia a geração do arquivo em uma thread separada"""
        # Capturar dados dos widgets ANTES de iniciar a thread
        bordero = self.entry_bordero.get()
        carteira = self.combobox_carteira.get()
        
        if not validar_bordero(bordero):
            self.atualizar_status("Erro: Número de Borderô inválido!", "error")
            return

        # Obter o ID da carteira selecionada
        carteira_id = None
        if carteira == "Carteira FIDC":
            carteira_id = self.settings.carteira_fidc_id
        elif carteira == "Carteira Própria":
            carteira_id = self.settings.carteira_propria_id

        # Desabilitar controles ANTES de iniciar a thread
        self.entry_bordero.config(state="disabled")
        self.combobox_carteira.config(state="disabled")
        self.gerar_botao.config(state="disabled")

        def processo_geracao():
            try:
                # Usar root.after() para atualizações de UI thread-safe
                self.root.after(0, lambda: self.atualizar_status("Conectando ao banco de dados...", "info"))
                self.root.after(0, lambda: self.mostrar_progresso(20))

                self.root.after(0, lambda: self.atualizar_status("Executando consulta...", "info"))
                self.root.after(0, lambda: self.mostrar_progresso(40))

                # Executa a consulta
                dados = self.bordero_service.consultar_bordero(bordero, carteira_id)
                
                if not dados:
                    self.root.after(0, lambda: self.atualizar_status("Erro: Nenhum dado retornado para o Borderô.", "error"))
                    return

                # Salvar dados da consulta para uso posterior
                self.dados_ultima_consulta = dados

                # Calcular resumo da situação dos títulos
                total_titulos = len(dados)
                titulos_pagos = sum(1 for d in dados if d.get('Situacao') == 'PAGO')
                titulos_abertos = total_titulos - titulos_pagos
                
                # Mostrar resumo da situação
                resumo_situacao = f"Total: {total_titulos} | PAGOS: {titulos_pagos} | EM ABERTO: {titulos_abertos}"
                self.root.after(0, lambda: self.atualizar_status(f"Consulta concluída - {resumo_situacao}", "info"))

                self.root.after(0, lambda: self.mostrar_progresso(60))
                
                # Selecionar nome do arquivo para salvar - usar flag para solicitar na thread principal
                self.root.after(0, lambda: self.atualizar_status("Selecionando arquivo para salvar...", "info"))
                self.root.after(0, lambda: self.mostrar_progresso(70))
                
                # Usar uma flag para solicitar o dialog na thread principal
                self.solicitar_arquivo = True
                self.dados_para_geracao = dados
                self.bordero_para_geracao = bordero
                
                # Aguardar resposta da thread principal
                while hasattr(self, 'solicitar_arquivo') and self.solicitar_arquivo:
                    import time
                    time.sleep(0.1)
                
                # Verificar se o usuário cancelou
                if not hasattr(self, 'arquivo_selecionado') or not self.arquivo_selecionado:
                    self.root.after(0, lambda: self.atualizar_status("Geração cancelada pelo usuário.", "info"))
                    return

                # Continuar com a geração
                self.root.after(0, lambda: self.atualizar_status("Gerando arquivo, aguarde...", "info"))
                self.root.after(0, lambda: self.mostrar_progresso(80))

                # Gera o arquivo remessa de posições
                self.file_service.gerar_arquivo(dados, self.arquivo_selecionado)
                self.arquivo_salvo = self.arquivo_selecionado
                
                # Criar backup do arquivo
                backup_path = self.backup_service.criar_backup(self.arquivo_selecionado, bordero)
                
                # Reabilita o botão de geração
                self.root.after(0, lambda: self.abrir_botao.config(state="normal"))

                # Atualiza a barra de progresso e a mensagem de status
                self.root.after(0, lambda: self.mostrar_progresso(100))
                self.root.after(0, lambda: self.atualizar_status("Arquivo gerado com sucesso!", "success"))
                
                # Adicionar ao histórico com informação do backup
                info_backup = f" (Backup: {os.path.basename(backup_path)})" if backup_path else ""
                self.history_service.adicionar_historico(f"Arquivo gerado: {self.arquivo_selecionado} (Borderô: {bordero}){info_backup}")
                self.root.after(0, self.atualizar_lista_historico)
                
            except Exception as e:
                self.root.after(0, lambda: self.atualizar_status(f"Erro: {str(e)}", "error"))
            finally:
                # Reabilitar controles
                self.root.after(0, lambda: self.entry_bordero.config(state="normal"))
                self.root.after(0, lambda: self.combobox_carteira.config(state="readonly"))
                self.root.after(0, lambda: self.gerar_botao.config(state="normal"))
                self.root.after(0, lambda: self.entry_bordero.focus())
                self.root.after(0, lambda: self.mostrar_progresso(0))

        # Iniciar processo em thread separada
        threading.Thread(target=processo_geracao, daemon=True).start()
    
    def verificar_solicitacao_arquivo(self):
        """Verifica se há solicitação de arquivo e abre o dialog na thread principal"""
        if hasattr(self, 'solicitar_arquivo') and self.solicitar_arquivo:
            self.solicitar_arquivo = False
            
            arquivo_nome = filedialog.asksaveasfilename(
                title="Salvar Arquivo de Posições",
                defaultextension=".txt",
                filetypes=[("Arquivos de Texto", "*.txt")]
            )
            
            if arquivo_nome:
                self.arquivo_selecionado = arquivo_nome
            else:
                self.arquivo_selecionado = None
        
        # Agendar próxima verificação
        self.root.after(100, self.verificar_solicitacao_arquivo)
    
    def abrir_backup(self):
        """Abre a janela para selecionar e abrir um arquivo de backup"""
        try:
            # Verificar se existem backups
            backups = list(Path("backups").glob("*"))
            if not backups:
                messagebox.showinfo("Informação", "Não há arquivos de backup disponíveis.")
                return
                
            # Criar janela de seleção
            backup_window = tk.Toplevel(self.root)
            backup_window.title("Selecionar Arquivo de Backup")
            backup_window.geometry("600x400")
            backup_window.transient(self.root)
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
                    self.history_service.adicionar_historico(f"Arquivo de backup aberto: {arquivo_backup.name}")
                    self.atualizar_lista_historico()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {e}")
            
            # Botões
            ttk.Button(button_frame, text="Abrir", command=abrir_arquivo_selecionado).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancelar", command=backup_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Duplo clique para abrir
            backup_listbox.bind("<Double-1>", lambda e: abrir_arquivo_selecionado())
            
        except Exception as e:
            self.atualizar_status(f"Erro ao abrir janela de backups: {e}", "error")
    
    def limpar_historico_e_backups(self):
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
            self.history_service.limpar_historico()
            self.atualizar_lista_historico()
            
            # Limpar arquivos de backup
            for arquivo in Path("backups").glob("*"):
                if arquivo.is_file():
                    arquivo.unlink()
                    
            self.atualizar_status("Histórico e backups limpos com sucesso!", "success")
        except Exception as e:
            self.atualizar_status(f"Erro ao limpar histórico e backups: {e}", "error")
    
    def mostrar_detalhes_situacao(self, dados):
        """Mostra uma janela com detalhes da situação de cada título"""
        if not dados:
            messagebox.showinfo("Informação", "Nenhum dado disponível para mostrar.")
            return
            
        # Criar janela de detalhes
        detalhes_window = tk.Toplevel(self.root)
        detalhes_window.title("Detalhes da Situação dos Títulos")
        detalhes_window.geometry("800x600")
        detalhes_window.transient(self.root)
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
    
    def mostrar_configuracoes(self):
        """Mostra as configurações carregadas (para debug)"""
        from ..utils.config_utils import verificar_configuracoes_banco
        
        config_ok, config_msg = verificar_configuracoes_banco(self.settings)
        
        info = f"Status das Configurações:\n{config_msg}\n\n"
        info += f"DB_SERVER: {'✓' if self.settings.db_server else '✗'} {self.settings.db_server or 'Não configurado'}\n"
        info += f"DB_NAME: {'✓' if self.settings.db_name else '✗'} {self.settings.db_name or 'Não configurado'}\n"
        info += f"DB_USER: {'✓' if self.settings.db_user else '✗'} {self.settings.db_user or 'Não configurado'}\n"
        info += f"DB_PASSWORD: {'✓' if self.settings.db_password else '✗'} {'***' if self.settings.db_password else 'Não configurado'}\n\n"
        info += f"Executável: {'Sim' if getattr(sys, 'frozen', False) else 'Não'}\n"
        info += f"Diretório atual: {os.getcwd()}"
        
        messagebox.showinfo("Configurações", info)
    
    def sobre(self):
        """Mostra informações sobre a aplicação"""
        messagebox.showinfo(
            f"Sobre - {self.settings.app_name}",
            f"{self.settings.app_name}\nVersão {self.settings.app_version}\n\nDesenvolvido por Arthur Morais\n© {datetime.now().year} Todos os direitos reservados\n"
        )
    
    def atualizar_status(self, mensagem, tipo="info"):
        """Atualiza a mensagem de status na barra inferior"""
        if not self.status_label:
            print(mensagem)
            return
            
        self.status_label.config(text=mensagem)
        if tipo == "error":
            self.status_label.config(foreground="red")
        elif tipo == "success":
            self.status_label.config(foreground="green")
        elif tipo == "warning":
            self.status_label.config(foreground="orange")
        else:
            self.status_label.config(foreground="black")
        self.root.update_idletasks()
    
    def mostrar_progresso(self, progresso):
        """Atualiza a barra de progresso"""
        if not self.progress_bar:
            return
            
        self.progress_bar["value"] = progresso
        self.root.update_idletasks()
    
    def run(self):
        """Executa a janela principal"""
        self.root.mainloop()