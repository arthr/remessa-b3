# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.3.0] - 2025-03-12
### Novidades

- Implementado mecanismo de sinalização para atualizações automáticas
- Adicionada verificação periódica de sinal de atualização na aplicação principal

### Correções

- Corrigido problema onde a aplicação principal não era encerrada automaticamente durante atualizações
- Melhorada documentação sobre o sistema de atualização

### Instruções de Atualização

1. Baixe o novo executável
2. Substitua o executável antigo pelo novo
3. Seus dados e configurações serão preservados

## [1.2.0] - 2025-03-10

### Adicionado
- Sistema de configuração via arquivo .env
- Suporte para múltiplos layouts de arquivo
- Splash Screen durante inicialização da aplicação
- Script para geração automática de imagem de splash

### Melhorado
- Interface de usuário com novos ícones
- Performance na geração de arquivos grandes
- Inicialização da aplicação com feedback visual
- Segurança com remoção de credenciais hardcoded

### Corrigido
- Erro ao processar borderôs com caracteres especiais
- Problema de conexão com bancos de dados remotos

## [1.1.0] - 2025-03-10

### Adicionado
- Sistema de backup automático dos arquivos gerados
- Interface para visualização e gerenciamento de backups
- Verificação automática de atualizações via GitHub Releases
- Opção para limpar histórico e backups

### Melhorado
- Interface de usuário com tema moderno
- Feedback visual durante operações
- Tratamento de erros mais detalhado

## [1.0.0] - 2024-11-28

### Adicionado
- Funcionalidade inicial de geração de arquivos para B3
- Filtro por carteira (FIDC, Própria ou Todas)
- Histórico de operações
- Interface gráfica básica 