from src.engine import CartolaEngine
import pandas as pd

# Carregar engine
file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
engine = CartolaEngine(file_path)

# Testar o confronto problemático
mandante = "RED BULL BRAGANTINO"
visitante = "ATLÉTICO-MG"  # Ou "ATLÉTICO" ou outro alias
window_n = 1
rodada = 2

print(f"\n{'='*80}")
print(f"TESTANDO: {mandante} vs {visitante} - Rodada {rodada}, Janela N={window_n}")
print(f"{'='*80}\n")

# Tentar variações de nome do Atlético
for visit_name in ["ATLÉTICO-MG", "ATLÉTICO", "Atlético-MG", "ATLETICO-MG"]:
    try:
        result = engine.generate_confronto_table(
            mandante=mandante,
            visitante=visit_name,
            window_n=window_n,
            mando_mode="POR_MANDO",
            rodada_curr=rodada
        )
        
        print(f"\n✅ Visitante: '{visit_name}' - FUNCIONOU!")
        print(f"COC_BASICA (Mandante Casa): {result['COC_BASICA']:.4f}")
        print(f"CDF_BASICA (Cedido pelo Visitante): {result['CDF_BASICA']:.4f}")
        print(f"COF_BASICA (Visitante Fora): {result['COF_BASICA']:.4f}")
        print(f"CDC_BASICA (Cedido pelo Mandante): {result['CDC_BASICA']:.4f}")
        
        # Agora vamos auditar: quem são os meias que foram contabilizados?
        df_raw = engine.get_meias_stats_raw(result.get('_date_cutoff'))
        
        print(f"\n📊 Total de meias na base (antes cutoff): {len(df_raw)}")
        
        # Meias do mandante jogando em casa
        meias_mand_casa = df_raw[(df_raw['TIME'] == mandante) & (df_raw['MANDO'] == 'CASA')]
        print(f"\n🏠 Meias do {mandante} jogando EM CASA:")
        if len(meias_mand_casa) > 0:
            print(meias_mand_casa[['NOME', 'DATA', 'ADVERSARIO', 'BASICA']].tail(window_n))
        else:
            print("  ❌ NENHUM ENCONTRADO!")
        
        # Meias do visitante jogando fora
        meias_vis_fora = df_raw[(df_raw['TIME'] == visit_name) & (df_raw['MANDO'] == 'FORA')]
        print(f"\n✈️  Meias do {visit_name} jogando FORA:")
        if len(meias_vis_fora) > 0:
            print(meias_vis_fora[['NOME', 'DATA', 'ADVERSARIO', 'BASICA']].tail(window_n))
        else:
            print("  ❌ NENHUM ENCONTRADO!")
            
        break  # Saímos após encontrar o nome correto
    except Exception as e:
        print(f"❌ Visitante: '{visit_name}' - ERRO: {e}")

print(f"\n{'='*80}\n")
