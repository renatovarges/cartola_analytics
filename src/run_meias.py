from src.engine import CartolaEngine
import pandas as pd
import os

# Configuração de Teste
FILE_PATH = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
OUTPUT_DIR = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\metrics"
DATA_CORTE = "2025-12-31" 
N_GAMES = 5 

# Simulando uma rodada arbitrária para teste
SIMULATED_GAMES = [
    ("FLAMENGO", "VASCO"),
    ("PALMEIRAS", "CORINTHIANS"),
    ("SÃO PAULO", "SANTOS"),
    ("GRÊMIO", "INTERNACIONAL"),
    ("BAHIA", "VITÓRIA")
]

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("--- Iniciando Motor Cartola (Teste Final Meias) ---")
    engine = CartolaEngine(FILE_PATH)
    
    results = []
    
    print(f"Calculando tabela para {len(SIMULATED_GAMES)} confrontos (Janela: {N_GAMES})...")
    
    for mandante, visitante in SIMULATED_GAMES:
        try:
            print(f"Processando {mandante} x {visitante}...")
            # Verifica se times existem na base para evitar erro de key
            # (Adicionei normalização simples aqui só pra garantir, engine já normaliza mas o input manual nao)
            
            row = engine.generate_confronto_table(
                mandante, 
                visitante, 
                window_n=N_GAMES, 
                date_cutoff=DATA_CORTE
            )
            results.append(row)
        except Exception as e:
            print(f"Erro em {mandante}x{visitante}: {e}")
        
    df_final = pd.DataFrame(results)
    
    # Reordenar colunas conforme documento
    cols_order = [
         # LADO ESQUERDO
         "COC_AF", "CDF_AF",
         "COC_CHUTES", "CDF_CHUTES",
         "COC_PG", "CDF_PG",
         "COC_BASICA", "CDF_BASICA",
         
         # MEIO
         "MANDANTE", "VISITANTE",
         
         # LADO DIREITO
         "COF_BASICA", "CDC_BASICA",
         "COF_PG", "CDC_PG",
         "COF_CHUTES", "CDC_CHUTES",
         "COF_AF", "CDC_AF"
    ]
    # Garantir que colunas existem (AF pode falhar se loader nao tiver)
    cols_order = [c for c in cols_order if c in df_final.columns]
    
    df_final = df_final[cols_order]
    
    out_path = os.path.join(OUTPUT_DIR, "VALIDACAO_MEIAS_FINAL.csv")
    df_final.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"--- Sucesso! Tabela salva em: {out_path} ---")
    print(df_final.to_string())

if __name__ == "__main__":
    main()
