from src.engine import CartolaEngine
from src.renderer_v2 import render_laterais_table
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Usar planilha padrão
INPUT_FILE = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

print("=== TESTE FINAL COM TIMESTAMP ===\n")
print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

engine = CartolaEngine(INPUT_FILE)

# Gerar dados para Cruzeiro x Coritiba
result = engine.generate_laterais_table("CRUZEIRO", "CORITIBA", window_n=5, mando_mode="POR_MANDO")

print("Valores retornados pelo engine:")
print(f"CDF_LE_DE: {result['CDF_LE_DE']}")
print(f"CDF_LD_DE: {result['CDF_LD_DE']}")
print(f"CDC_LE_DE: {result['CDC_LE_DE']}")
print(f"CDC_LD_DE: {result['CDC_LD_DE']}")

# Criar DataFrame
df = pd.DataFrame([result])

# Renderizar
fig = render_laterais_table(df, rodada_num=2, window_n=5, tipo_filtro="POR_MANDO")

# Salvar com timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"LATERAIS_TESTE_{timestamp}.png"

fig.savefig(output_file, dpi=600, bbox_inches='tight', facecolor='white')
plt.close(fig)

print(f"\n✓ Imagem salva: {output_file}")
print(f"\nSe esta imagem AINDA mostrar '4', então há um problema no RENDERER.")
print(f"Se mostrar '0', então o problema é CACHE do navegador/Streamlit.")
