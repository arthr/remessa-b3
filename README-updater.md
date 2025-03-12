# Sistema de Atualização Dual para Remessa B3

Este projeto implementa um sistema de atualização dual para o aplicativo Remessa B3, dividindo a responsabilidade de atualização entre o aplicativo principal (`app.py`) e um componente dedicado (`updater.py`).

## Estrutura

- **app.py**: Aplicativo principal que verifica atualizações e inicia o atualizador quando necessário.
- **updater.py**: Aplicativo secundário responsável por baixar e instalar as atualizações.
- **updater.spec**: Arquivo de configuração do PyInstaller para compilar o atualizador.

## Funcionamento

1. O aplicativo principal verifica automaticamente se há atualizações disponíveis na inicialização (ou quando solicitado).
2. Ao encontrar uma atualização, exibe uma janela com informações sobre a nova versão e opções para o usuário.
3. Se o usuário escolher "Baixar e Instalar Automaticamente", o aplicativo principal executa o `updater.py/updater.exe`.
4. O atualizador (`updater.py`) encarrega-se de:
   - Baixar a atualização do GitHub
   - Exibir o progresso e a velocidade do download
   - Criar um script batch para substituir o executável principal
   - Reiniciar o aplicativo atualizado

## Compilação

Para compilar os executáveis, você precisará do PyInstaller instalado (`pip install pyinstaller`).

### Compilando o Atualizador

```bash
pyinstaller updater.spec
```

### Compilando o Aplicativo Principal

Certifique-se de incluir o updater.exe com o seu aplicativo principal.

```bash
pyinstaller --name "remessa-b3" --onefile --windowed --icon=favicon-b3.ico app.py
```

Após a compilação, copie o `updater.exe` da pasta `dist` para o mesmo diretório onde está o `remessa-b3.exe`.

## Dicas para Distribuição

1. Ao criar releases no GitHub, inclua ambos os executáveis (`remessa-b3.exe` e `updater.exe`).
2. O arquivo `remessa-b3.exe` deve ser o asset principal marcado para download.
3. O sistema detecta automaticamente se está rodando em modo de desenvolvimento ou como executável compilado.

## Solução de Problemas

- **Erro "Atualizador não encontrado"**: Verifique se o arquivo `updater.exe` está no mesmo diretório que o aplicativo principal.
- **Permissões de Escrita**: O atualizador precisa de permissões para escrever no diretório onde o aplicativo principal está instalado.
- **Modo Desenvolvimento**: Em modo de desenvolvimento, o atualizador pode ser executado, mas não substituirá arquivos. 