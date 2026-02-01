@echo off
echo Encerrando processos Python antigos...
taskkill /F /IM python.exe >nul 2>&1
echo.
echo Iniciando Cartola Analytics...
echo Por favor, aguarde e NAO feche esta janela.
echo O navegador deve abrir automaticamente em alguns segundos.
echo.
cd /d "%~dp0"
streamlit run src/app.py --server.port 8501
pause
