@echo off
setLocal EnableDelayedExpansion
chcp 65001 >nul
echo ========================================
echo    COMPILANDO REMESSA B3 - BUILD COMPLETO
echo ========================================
echo.

REM Limpar pastas de build anteriores
echo [1/6] Limpando pastas de build anteriores...
if exist "build" rmdir /S /Q build
if exist "dist" rmdir /S /Q dist
echo Limpeza concluida
echo.

REM Verificar arquivos de recursos
echo [2/6] Verificando arquivos de recursos...
if not exist "splashLogo.png" (
    echo ERRO: splashLogo.png nao encontrado!
    echo Execute: python create_splash.py
    exit /b 1
)
if not exist "favicon-b3.ico" (
    echo ERRO: favicon-b3.ico nao encontrado!
    exit /b 1
)
if not exist ".env" (
    echo ERRO: .env nao encontrado!
    echo Copie o arquivo .env.example para .env e configure
    exit /b 1
)
echo Recursos verificados
echo.

REM Verificar se o PyInstaller está instalado
echo [3/6] Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERRO: PyInstaller nao encontrado!
    echo Execute: pip install pyinstaller
    exit /b 1
)
echo PyInstaller encontrado
echo.

REM Compilar aplicação principal
echo [4/6] Compilando aplicacao principal (remessa-b3.exe)...
pyinstaller remessa-b3.spec
if errorlevel 1 (
    echo ERRO: Falha na compilacao da aplicacao principal!
    exit /b 1
)
echo Aplicacao principal compilada
echo.

REM Compilar updater
echo [5/6] Compilando sistema de atualizacao (updater.exe)...
pyinstaller updater.spec
if errorlevel 1 (
    echo AVISO: Falha na compilacao do updater!
    echo A aplicacao principal foi compilada, mas o updater falhou.
    echo Voce pode continuar sem o sistema de atualizacao.
    echo.
) else (
    echo Sistema de atualizacao compilado
    echo.
)

REM Verificar resultados finais
echo [6/6] Verificando resultados...
echo.

set BUILD_SUCCESS=false
if exist "dist\remessa-b3.exe" set BUILD_SUCCESS=true

if "!BUILD_SUCCESS!"=="true" goto :SUCCESSO

:FALHA
echo ========================================
echo    FALHA NO BUILD!
echo ========================================
echo.
echo Verifique os erros acima e tente novamente.
echo.
goto :END

:SUCCESSO
echo ========================================
echo    BUILD CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Executaveis gerados em: dist\
echo.
echo Arquivos criados:
if exist "dist\remessa-b3.exe" echo   - remessa-b3.exe (aplicacao principal)
if exist "dist\updater.exe" echo   - updater.exe (sistema de atualizacao)
echo.
echo Para distribuicao:
echo   1. Copie AMBOS os executaveis para a pasta de destino
echo   2. Mantenha ambos na mesma pasta
echo   3. Execute remessa-b3.exe para iniciar
echo.
echo Nota: O sistema de atualizacao requer ambos os arquivos
echo    para funcionar corretamente.
echo.

:END
echo Processo concluido.
echo.
pause