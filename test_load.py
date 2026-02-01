from src.loader import load_excel_data

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    data = load_excel_data(file_path)
    print("\n✅ SUCESSO! Dados carregados.")
    print(f"\n📊 Por Jogo: {len(data['por_jogo'])} linhas")
    print(f"Colunas: {list(data['por_jogo'].columns)}")
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
