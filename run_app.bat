@echo off
echo Iniciando Cartola Analytics...
echo Por favor, aguarde e NAO feche esta janela.
echo O navegador deve abrir automaticamente em alguns segundos.
echo.

:: Tenta rodar com py launcher primeiro
py -m streamlit run src/app.py
if %errorlevel% equ 0 goto end

:: Se falhar, tenta python direto
python -m streamlit run src/app.py

:end
pause
