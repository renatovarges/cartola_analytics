import os
import sys

# Adicionar src ao path
sys.path.append(os.path.abspath("src"))

try:
    import config
    print(f"INPUT_DIR configurado: {config.INPUT_DIR}")
    
    files_to_check = [
        config.EXCEL_FILE,
        "classificacao_meias_volantes.csv"
    ]
    
    all_ok = True
    for f in files_to_check:
        full_path = os.path.join(config.INPUT_DIR, f)
        exists = os.path.exists(full_path)
        status = "✅" if exists else "❌"
        print(f"{status} {f}: {full_path}")
        if not exists: all_ok = False
        
    if all_ok:
        print("\nCONCLUSÃO: Todos os arquivos essenciais estão acessíveis.")
    else:
        print("\nCONCLUSÃO: Faltam arquivos!")

except Exception as e:
    print(f"Erro ao importar config: {e}")
