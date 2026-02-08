
from src.engine import CartolaEngine
from src.renderer_v2 import render_zagueiros_table
import pandas as pd
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")

# Jogos para teste
GAMES = [
    ("FLAMENGO", "INTERNACIONAL"),
    ("VASCO", "AMÉRICA-MG")
]

def main():
    print("--- Iniciando Teste Zagueiros ---")
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: Arquivo de input não encontrado: {INPUT_FILE}")
        return

    engine = CartolaEngine(INPUT_FILE)
    
    data = []
    for mandante, visitante in GAMES:
        try:
            print(f"Processando {mandante} x {visitante}...")
            # Zagueiros table generation might return a dict or similar structure
            # engine.generate_zagueiros_table needs to be checked if it exists/works
            # Assuming it exists based on renderer file existence
            row = engine.generate_zagueiros_table(
                mandante, visitante, 
                window_n=5, 
                mando_mode="POR_MANDO"
            )
            data.append(row)
        except Exception as e:
            print(f"Erro ao processar {mandante}x{visitante}: {e}")
            
    if not data:
        print("Nenhum dado gerado.")
        return

    df = pd.DataFrame(data)
    
    # Renderizar
    print("Renderizando Tabela Zagueiros...")
    try:
        fig = render_zagueiros_table(df, rodada_num=99, window_n=5, tipo_filtro="POR_MANDO")
        
        output_filename = "TABELA_ZAGUEIROS_TESTE.png"
        print(f"Salvando em {output_filename}...")
        fig.savefig(output_filename, dpi=300, bbox_inches='tight')
        print("Concluído com sucesso!")
    except Exception as e:
        print(f"ERRO AO RENDERIZAR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
