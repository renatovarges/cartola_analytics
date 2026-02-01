
import pandas as pd
import sys
import os

# Adjust path to find src
sys.path.append(os.getcwd())
from src.config import INPUT_DIR
from src.loader import load_data

try:
    df = load_data()
    print("--- DIAGNOSTIC START ---")
    print(f"Por Jogo Columns: {list(df.columns)}")
    
    # Load raw datasets again to check SCOUTS
    from src.loader import load_excel_data
    from src.config import INPUT_DIR, EXCEL_FILE
    import os
    
    fpath = os.path.join(INPUT_DIR, EXCEL_FILE)
    datasets = load_excel_data(fpath)
    
    if "SCOUTS" in datasets:
        print("--- SCOUTS TAB FOUND ---")
        df_sc = datasets["SCOUTS"]
        print(f"Scouts Columns: {list(df_sc.columns)}")
        print(df_sc.head(3).to_string())
    else:
        print("--- SCOUTS TAB NOT FOUND ---")
        
    print("--- ROWS WITH POSICAO=3 ---")
    df_zag = df[df["POSICAO"].astype(str) == "3"]
    print(f"Count: {len(df_zag)}")
    if len(df_zag) > 0:
        print(df_zag.head(2).to_string())
    else:
        print("No Zagueiros found with current filter.")
        
    print("--- DIAGNOSTIC END ---")
    
except Exception as e:
    print(f"Error: {e}")
