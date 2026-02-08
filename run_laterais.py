
from src.engine import CartolaEngine
from src.renderer_v2 import render_laterais_table
import pandas as pd
import matplotlib.pyplot as plt

import os
# Hardcoded path to avoid config import issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")

GAMES = [
    ("ATLÉTICO-MG", "PALMEIRAS"),
    ("MIRASSOL", "VASCO"),
    ("CORITIBA", "RED BULL BRAGANTINO"),
    ("FLUMINENSE", "GRÊMIO"),
    ("CORINTHIANS", "BAHIA"),
    ("CHAPECOENSE", "SANTOS"),
    ("SÃO PAULO", "FLAMENGO"),
    ("VITÓRIA", "REMO"),
    ("BOTAFOGO", "CRUZEIRO"),
    ("INTERNACIONAL", "ATHLETICO-PR")
]

def main():
    print("--- Iniciando Geração Tabela LATERAIS (600 DPI) ---")
    try:
        engine = CartolaEngine(INPUT_FILE)
    except Exception as e:
        print(f"Erro ao iniciar engine: {e}")
        return

    data = []
    for mandante, visitante in GAMES:
        try:
            print(f"Processando {mandante} x {visitante}...")
            # window_n=5, date_cutoff=None, mando_mode="POR_MANDO"
            row = engine.generate_laterais_table(
                mandante, visitante, 
                window_n=5, 
                mando_mode="POR_MANDO"
            )
            data.append(row)
        except Exception as e:
            print(f"Erro ao processar {mandante}x{visitante}: {e}")
            import traceback
            traceback.print_exc()
            
    if not data:
        print("Nenhum dado gerado.")
        return

    df = pd.DataFrame(data)
    
    # Reordenar colunas? O engine já entrega dict. O DF assume ordem das keys ou aleatório?
    # O renderer usa uma lista explicita `all_cols` para iterar, então a ordem do DF não importa tanto,
    # desde que os nomes das colunas batam.
    
    print("Renderizando Tabela...")
    try:
        fig = render_laterais_table(df, rodada_num=2, window_n=5, tipo_filtro="POR_MANDO")
        
        output_filename = "TABELA_LATERAIS_TESTE.png"
        print(f"Salvando em {output_filename} com DPI 600...")
        
        fig.savefig(output_filename, dpi=600, bbox_inches='tight')
        print("Concluído!")
    except Exception as e:
        print(f"Erro na renderização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
