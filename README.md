# Remessa B3 - Gerador de Arquivo

Aplicação para geração de arquivos de remessa para a B3 (Brasil, Bolsa, Balcão) a partir de dados extraídos de um banco de dados SQL Server.

## Sobre o Projeto

Esta aplicação foi desenvolvida para automatizar o processo de geração de arquivos de remessa para a B3, seguindo o layout específico exigido pela instituição. A aplicação consulta um banco de dados SQL Server, extrai as informações necessárias e formata os dados conforme as especificações da B3.

## Funcionalidades

- Geração de arquivos de remessa para B3
- Filtro por carteira (FIDC, Própria ou Todas)
- Histórico de operações
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

## Compilação

Para gerar um executável standalone:

```
pyinstaller remessa-b3.spec
```

O executável será gerado na pasta `dist/`.

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