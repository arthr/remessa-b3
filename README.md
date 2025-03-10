# Remessa B3 - Gerador de Arquivo

Aplicação para geração de arquivos de remessa para a B3 (Brasil, Bolsa, Balcão) a partir de dados extraídos de um banco de dados SQL Server.

## Sobre o Projeto

Esta aplicação foi desenvolvida para automatizar o processo de geração de arquivos de remessa para a B3, seguindo o layout específico exigido pela instituição. A aplicação consulta um banco de dados SQL Server, extrai as informações necessárias e formata os dados conforme as especificações da B3.

## Funcionalidades

- Geração de arquivos de remessa para B3
- Filtro por carteira (FIDC, Própria ou Todas)
- Histórico de operações
- Backup automático dos arquivos gerados
- Acesso a arquivos de backup anteriores
- Verificação automática de atualizações
- Configuração via arquivo .env
- Interface gráfica moderna e intuitiva
- Feedback visual do progresso
- Tratamento de erros

## Requisitos

- Python 3.8 ou superior
- SQL Server
- Driver ODBC para SQL Server

## Estrutura do Projeto

```
remessa-b3/
├── app.py                  # Arquivo principal da aplicação
├── requirements.txt        # Dependências do projeto
├── favicon-b3.ico          # Ícone da aplicação
├── remessa-b3.spec         # Configuração do PyInstaller
├── README.md               # Documentação do projeto
├── CHANGELOG.md            # Histórico de alterações
├── RELEASE.md              # Instruções para lançamento de versões
├── .env.example            # Exemplo de configuração (versionado)
├── .env                    # Configurações reais (não versionado)
├── backups/                # Pasta de backups dos arquivos gerados
└── venv/                   # Ambiente virtual (não versionado)
```

## Instalação para Desenvolvimento

1. Clone este repositório:
   ```
   git clone https://github.com/seu-usuario/remessa-b3.git
   cd remessa-b3
   ```

2. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```

3. Ative o ambiente virtual:
   ```
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

5. Configure o arquivo .env:
   ```
   # Copie o arquivo de exemplo
   cp .env.example .env
   
   # Edite o arquivo .env com suas configurações
   # Especialmente as credenciais do banco de dados
   ```

## Uso

1. Com o ambiente virtual ativado, execute a aplicação:
   ```
   python app.py
   ```

2. Na interface da aplicação:
   - Digite o número do Borderô
   - Selecione a carteira desejada (FIDC, Própria ou Todas)
   - Clique em "Gerar Arquivo"
   - Selecione onde salvar o arquivo gerado
   - Use o botão "Abrir Arquivo" para visualizar o resultado

3. Funcionalidade de Backup:
   - Cada arquivo gerado é automaticamente salvo como backup
   - Os backups são nomeados com o número do borderô e timestamp
   - Acesse os backups pelo menu "Arquivo > Abrir Arquivo de Backup" ou pelo botão "Abrir Backup"
   - Limpe o histórico e backups pelo menu "Arquivo > Limpar Histórico e Backups"

4. Sistema de Atualização:
   - A aplicação verifica automaticamente por novas versões ao iniciar
   - Você pode verificar manualmente através do menu "Ajuda > Verificar Atualizações"
   - Quando uma nova versão estiver disponível, você será notificado e poderá baixá-la diretamente

## Configuração (.env)

O arquivo `.env` contém todas as configurações da aplicação:

- **Banco de Dados**: Credenciais para conexão ao SQL Server
- **Aplicação**: Versão e nome da aplicação
- **GitHub**: Configurações para verificação de atualizações
- **Carteiras**: IDs das carteiras disponíveis
- **Layout B3**: Configurações específicas para o layout de arquivo B3

Para configurar, copie o arquivo `.env.example` para `.env` e edite conforme necessário.

## Compilação

Para gerar um executável standalone:

```
pyinstaller remessa-b3.spec
```

O executável será gerado na pasta `dist/`.

## Versionamento

O versionamento segue o padrão [SemVer](https://semver.org/):
- MAJOR.MINOR.PATCH (ex: 1.1.0)
- Versão MAJOR: mudanças incompatíveis com versões anteriores
- Versão MINOR: adição de funcionalidades compatíveis com versões anteriores
- Versão PATCH: correções de bugs compatíveis com versões anteriores

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Suporte

Para suporte ou dúvidas, entre em contato com o desenvolvedor.

## Desenvolvedor

Arthur Morais 