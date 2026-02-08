from src.engine import CartolaEngine
from src.renderer_v2 import render_atacantes_table
import pandas as pd
import matplotlib.pyplot as plt

import os
# Arquivo real
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")
engine = CartolaEngine(INPUT_FILE)

# Gerar dados Atacantes Cruzeiro x Coritiba (RODADA 2, usando N=1, filtro TODOS)
# mv_filter="ATACANTE"
try:
    result = engine.generate_confronto_table(
        "CRUZEIRO", "CORITIBA", 
        window_n=1, 
        date_cutoff=None, 
        mando_mode="TODOS", 
        rodada_curr=2,
        mv_filter="ATACANTE"
    )

    print("Dados Gerados (Atacantes):")
    print(f"Mandante: {result['MANDANTE']}")
    print(f"Visitante: {result['VISITANTE']}")
    print(f"COC_AF: {result['COC_AF']}")

    df = pd.DataFrame([result])

    # Renderizar
    fig = render_atacantes_table(df, rodada_num=2, window_n=1, tipo_filtro="gersl")

    # Salvar
    output_file = "PROVA_FINAL_ATACANTES.png"
    fig.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Imagem gerada: {output_file}")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
