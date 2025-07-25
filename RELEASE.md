# Instruções para Lançamento de Novas Versões

Este documento descreve o processo para lançar novas versões do Remessa B3 no GitHub.

## Processo de Versionamento

O projeto segue o padrão [SemVer](https://semver.org/) para versionamento:

- **MAJOR.MINOR.PATCH** (ex: 1.1.0)
- **MAJOR**: Mudanças incompatíveis com versões anteriores
- **MINOR**: Adição de funcionalidades compatíveis com versões anteriores
- **PATCH**: Correções de bugs compatíveis com versões anteriores

## Passos para Lançar uma Nova Versão

1. **Atualizar a Versão no Código**:
   - Abra o arquivo `app.py`
   - Atualize a constante `APP_VERSION` com o novo número de versão
   - Exemplo: `APP_VERSION = "1.2.0"`

2. **Atualizar o Changelog**:
   - Documente todas as alterações feitas nesta versão
   - Inclua novas funcionalidades, melhorias e correções de bugs

3. **Compilar a Aplicação**:
   ```
   ./build.bat
   ```

4. **Testar o Executável**:
   - Verifique se o executável gerado funciona corretamente
   - Teste todas as novas funcionalidades e correções
   - **Teste o sistema de atualização**:
     - Verifique se o mecanismo de sinalização funciona corretamente
     - Confirme que a aplicação encerra automaticamente quando atualizada

5. **Commit e Push das Alterações**:
   ```
   git add .
   git commit -m "Versão X.Y.Z"
   git push origin master
   ```

6. **Criar uma Tag para a Versão**:
   ```
   git tag -a vX.Y.Z -m "Versão X.Y.Z"
   git push origin vX.Y.Z
   ```

7. **Criar um Release no GitHub**:
   - Acesse a página do repositório no GitHub
   - Vá para a seção "Releases"
   - Clique em "Draft a new release"
   - Selecione a tag criada
   - Preencha o título com "Versão X.Y.Z"
   - Adicione as notas de lançamento (changelog)
   - Anexe o executável compilado
   - Publique o release

## Notas de Lançamento

As notas de lançamento devem seguir este formato:

```markdown
## Novidades

- Adicionada funcionalidade X
- Melhorada a interface Y

## Correções

- Corrigido bug Z
- Resolvido problema W

## Instruções de Atualização

1. Baixe o novo executável
2. Substitua o executável antigo pelo novo
3. Seus dados e configurações serão preservados
```

## Verificação de Atualizações

A aplicação verifica automaticamente por novas versões ao iniciar, consultando a API do GitHub. Quando uma nova versão é detectada, o usuário é notificado e pode baixá-la diretamente.