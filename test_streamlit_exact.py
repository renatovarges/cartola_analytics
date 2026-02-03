import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
import pandas as pd

# Usar EXATAMENTE a mesma planilha que o Streamlit
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(BASE_DIR, "input", "Scouts_Reorganizado.xlsx")

print("=== SIMULAÇÃO EXATA DO STREAMLIT ===\n")
print(f"Arquivo: {DEFAULT_PATH}\n")

# Inicializar engine
engine = CartolaEngine(DEFAULT_PATH)

# Simular o que o app faz quando você clica em "Gerar Tabela"
# Usando os mesmos jogos que aparecem na sua imagem

jogos = [
    ("FLAMENGO", "INTERNACIONAL"),
    ("VASCO", "CHAPECOENSE"),
    ("SANTOS", "SÃO PAULO"),
    ("PALMEIRAS", "VITÓRIA"),
    ("RED BULL BRAGANTINO", "ATLÉTICO-MG"),
    ("CRUZEIRO", "CORITIBA"),  # ← ESTE É O JOGO QUE VOCÊ MOSTROU!
]

results = []

for mandante, visitante in jogos:
    print(f"Processando {mandante} x {visitante}...")
    try:
        row = engine.generate_laterais_table(mandante, visitante, window_n=5, mando_mode="POR_MANDO")
        results.append(row)
    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()

# Criar DataFrame como o Streamlit faz
df = pd.DataFrame(results)

print("\n=== RESULTADO ===")
print(f"Total de jogos processados: {len(df)}")

# Encontrar linha do Cruzeiro x Coritiba
linha_cruzeiro = df[(df['MANDANTE'] == 'CRUZEIRO') & (df['VISITANTE'] == 'CORITIBA')]

if len(linha_cruzeiro) > 0:
    print("\n--- CRUZEIRO x CORITIBA ---")
    print(f"CDF_LE_DE (Desarmes cedidos LE pelo Cruzeiro): {linha_cruzeiro['CDF_LE_DE'].iloc[0]}")
    print(f"CDF_LD_DE (Desarmes cedidos LD pelo Cruzeiro): {linha_cruzeiro['CDF_LD_DE'].iloc[0]}")
    print(f"CDC_LE_DE (Desarmes cedidos LE pelo Coritiba): {linha_cruzeiro['CDC_LE_DE'].iloc[0]}")
    print(f"CDC_LD_DE (Desarmes cedidos LD pelo Coritiba): {linha_cruzeiro['CDC_LD_DE'].iloc[0]}")
    
    print("\n--- TODOS OS VALORES DESTA LINHA ---")
    for col in linha_cruzeiro.columns:
        if 'LE' in col or 'LD' in col or 'SG' in col:
            print(f"{col}: {linha_cruzeiro[col].iloc[0]}")
else:
    print("\n❌ Linha não encontrada!")

# Salvar CSV para comparação
df.to_csv("debug_laterais_output.csv", index=False)
print("\n✓ Dados salvos em debug_laterais_output.csv")
