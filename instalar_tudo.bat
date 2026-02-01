@echo off
echo ==========================================
echo Instalando dependencias do Cartola Analytics...
echo ==========================================
echo.

echo Tentando instalar usando 'py' launch (Recomendado)...
py -m pip install -r requirements.txt
if %errorlevel% equ 0 goto success

echo.
echo 'py' falhou. Tentando 'python' direto...
python -m pip install -r requirements.txt
if %errorlevel% equ 0 goto success

echo.
echo ==========================================
echo ERRO FATAL: Nao foi possivel encontrar o Python.
echo Por favor, instale o Python marcando a opcao "Add Python to PATH".
echo ==========================================
pause
exit /b

:success
echo.
echo ==========================================
echo SUCESSO! Tudo instalado.
echo Agora voce pode rodar o 'run_app.bat'.
echo ==========================================
pause
