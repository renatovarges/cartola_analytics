import pandas as pd
import os

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"

try:
    print(f"Reading file: {file_path}")
    # Read just the header and a few rows to be fast
    df = pd.read_excel(file_path, nrows=5)
    
    print("\n--- Columns ---")
    for col in df.columns:
        print(col)
        
    print("\n--- Data Types ---")
    print(df.dtypes)
    
    print("\n--- Head (first 3 rows) ---")
    print(df.head(3).to_string())

except Exception as e:
    print(f"Error reading excel: {e}")
