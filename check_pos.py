from src import loader
import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
datasets = loader.load_excel_data(file_path)
df = datasets["POR_JOGO"]

if "POSICAO" in df.columns:
    print("Posições encontradas:", df["POSICAO"].unique())
else:
    print("Coluna POSICAO ainda não encontrada.")
