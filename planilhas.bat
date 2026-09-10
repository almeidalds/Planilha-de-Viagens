@echo off
title Painel Logistico CTM
echo Iniciando o Sistema de Viagens CTM...
echo Aguarde um momento enquanto o servidor e carregado.
@REM  Adicione o caminho do sistema abaixo
cd /d "C:\Users\Almeidalds\Documents\GitHub - CTM\viagens"
call .venv\Scripts\activate
streamlit run app.py