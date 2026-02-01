import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\DIVISÃO VOLANTES E MEIAS.xlsx"
df = pd.read_excel(file_path)

print("="*80)
print("ESTRUTURA DO ARQUIVO")
print("="*80)
print(f"\nShape: {df.shape}")
print(f"\nColunas: {list(df.columns)}")

print("\n" + "="*80)
print("PRIMEIRAS 20 LINHAS COMPLETAS")
print("="*80)
print(df.head(20).to_string())

print("\n" + "="*80)
print("VALORES ÚNICOS POR COLUNA (primeiras 10)")
print("="*80)
for i, col in enumerate(df.columns):
    unique_vals = df[col].dropna().unique()[:10]
    print(f"\nColuna {i} ({col}):")
    print(f"  Valores únicos: {list(unique_vals)}")
