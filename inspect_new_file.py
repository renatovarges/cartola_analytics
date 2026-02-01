import pandas as pd

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\API CARTOLA RODADA 1.xlsx"
xls = pd.ExcelFile(file_path)

print(f"ABAS: {xls.sheet_names}\n")

for sheet in xls.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet, nrows=3)
    print(f"=== ABA: {sheet} ===")
    print(f"Total colunas: {len(df.columns)}")
    print("Colunas:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: '{col}'")
    print(f"\nPrimeiras linhas:")
    print(df.head(2))
    print("\n" + "="*80 + "\n")
