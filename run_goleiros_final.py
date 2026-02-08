
from src.engine import CartolaEngine
from src.renderer_v2 import render_goleiros_table
import pandas as pd
import matplotlib.pyplot as plt
import os
# from src.config import FILE_PATH as INPUT_FILE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")

# Jogos para teste (Rodada Fictícia ou Real)
# Lista de tuplas (Mandante, Visitante)
GAMES = [
    ("FLAMENGO", "INTERNACIONAL"),
    ("VASCO", "AMÉRICA-MG"), # Ajustado para times que tenham dados ou generic
    ("SANTOS", "SÃO PAULO"),
    ("PALMEIRAS", "ATHLETICO-PR"),
    ("RB BRAGANTINO", "ATLÉTICO-MG"),
    ("CRUZEIRO", "CORITIBA"),
    ("GRÊMIO", "BOTAFOGO"),
    ("ATHLETICO-PR", "CORINTHIANS"), # Repetido? Nao, mudando
    ("BAHIA", "FLUMINENSE"),
    ("REMO", "MIRASSOL") # Times variados
]
# Nota: engine.generate_goleiros_table vai tentar achar dados. 
# Se nao achar, retorna zeros, mas não quebra (blindagem).
# Para garantir visual bonito, usaremos times conhecidos do Brasileirão da base.

def main():
    print("--- Iniciando Geração Final Goleiros (HD) ---")
    engine = CartolaEngine(INPUT_FILE)
    
    data = []
    for mandante, visitante in GAMES:
        try:
            print(f"Processando {mandante} x {visitante}...")
            row = engine.generate_goleiros_table(
                mandante, visitante, 
                window_n=5, 
                mando_mode="POR_MANDO"
            )
            data.append(row)
        except Exception as e:
            print(f"Erro ao processar {mandante}x{visitante}: {e}")
            
    df = pd.DataFrame(data)
    
    # Renderizar
    print("Renderizando Tabela...")
    # dpi=300 já garantido no savefig, mas o renderer define dpi=600 no figure.
    fig = render_goleiros_table(df, rodada_num=2, window_n=5, tipo_filtro="POR_MANDO")
    
    output_filename = "TABELA_GOLEIROS_FINAL_HD.png"
    print(f"Salvando em {output_filename} com DPI 600...")
    
    fig.savefig(output_filename, dpi=600, bbox_inches='tight')
    print("Concluído!")

if __name__ == "__main__":
    main()
