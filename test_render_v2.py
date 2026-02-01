import pandas as pd
import matplotlib.pyplot as plt
from src.renderer_v2 import render_meias_table
import os

# Dummy Data
data = {
    "MANDANTE": ["Flamengo", "Palmeiras"],
    "VISITANTE": ["Vasco", "Santos"],
    "COC_AF": [5, 2],
    "CDF_AF": [3, 4],
    "COC_CHUTES": [10, 8],
    "CDF_CHUTES": [9, 7],
    "COC_PG": [15, 12],
    "CDF_PG": [14, 11],
    "COC_BASICA": [4.5, 3.2],
    "CDF_BASICA": [3.8, 4.0],
    "MANDO": ["CASA", "CASA"],
    "COF_AF": [1, 2],
    "CDC_AF": [3, 1],
    "COF_CHUTES": [5, 6],
    "CDC_CHUTES": [7, 8],
    "COF_PG": [10, 10],
    "CDC_PG": [5, 5],
    "COF_BASICA": [4.0, 3.5],
    "CDC_BASICA": [2.5, 3.0]
}

df = pd.DataFrame(data)

print("Testing renderer with legend...")
try:
    fig = render_meias_table(df, rodada_num=1, window_n=5, tipo_filtro="TODOS", exibir_legenda=True)
    output_path = "test_output.png"
    fig.savefig(output_path, dpi=400)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"Success! Image generated. Size: {size/1024:.2f} KB")
        # cleanup
        os.remove(output_path)
    else:
        print("Error: File not created.")
except Exception as e:
    print(f"Error during rendering: {e}")
    import traceback
    traceback.print_exc()
