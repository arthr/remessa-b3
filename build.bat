@echo off
echo Compilando Remessa B3...
echo.

REM Limpar pastas de build anteriores
echo Limpando pastas de build anteriores...
if exist "build" rmdir /S /Q build
if exist "dist" rmdir /S /Q dist
echo.

REM Verificar arquivos de recursos
echo Verificando arquivos de recursos...
if not exist "splashLogo.png" (
    echo ERRO: splashLogo.png não encontrado!
    exit /b 1
)
if not exist "favicon-b3.ico" (
    echo ERRO: favicon-b3.ico não encontrado!
    exit /b 1
)
echo.

REM Executar o PyInstaller com o arquivo spec
echo Compilando com PyInstaller...
pyinstaller remessa-b3.spec
echo.

REM Verificar se a compilação foi bem-sucedida
if exist "dist\remessa-b3.exe" (
    echo Compilação concluída com sucesso!
    echo Executável gerado em: dist\remessa-b3.exe
) else (
    echo ERRO: Falha na compilação.
)

echo.
echo Processo concluído. 