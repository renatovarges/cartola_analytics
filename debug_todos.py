from src.engine import CartolaEngine
import pandas as pd

# Carregar engine
file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
engine = CartolaEngine(file_path)

# Testar com TODOS
mandante = "RED BULL BRAGANTINO"
visitante = "ATLÉTICO-MG"
window_n = 1
rodada = 2

print(f"\n{'='*80}")
print(f"TESTANDO COM FILTRO 'TODOS': {mandante} vs {visitante}")
print(f"Rodada {rodada}, Janela N={window_n}")
print(f"{'='*80}\n")

result = engine.generate_confronto_table(
    mandante=mandante,
    visitante=visitante,
    window_n=window_n,
    mando_mode="TODOS",  # <<<< TODOS, não POR_MANDO
    rodada_curr=rodada
)

print(f"COC_BASICA (Mandante geral): {result['COC_BASICA']:.4f}")
print(f"CDF_BASICA (Cedido pelo Visitante): {result['CDF_BASICA']:.4f}")
print(f"COF_BASICA (Visitante geral): {result['COF_BASICA']:.4f}")
print(f"CDC_BASICA (Cedido pelo Mandante): {result['CDC_BASICA']:.4f}")

# Debug detalhado
df_raw = engine.get_meias_stats_raw()

print(f"\n{'='*80}")
print("DEBUG DETALHADO:")
print(f"{'='*80}\n")

# 1. Meias do Red Bull Bragantino (mandante) - QUALQUER mando
meias_mand = df_raw[df_raw['TIME'] == mandante]
print(f"🔴 Meias do {mandante} (TODOS os jogos):")
if len(meias_mand) > 0:
    print(meias_mand[['NOME', 'DATA', 'MANDO', 'ADVERSARIO', 'BASICA']].tail(window_n))
    print(f"   → Média BASICA: {meias_mand.groupby('MATCH_ID')['BASICA'].mean().tail(window_n).mean():.4f}")
else:
    print("  ❌ NENHUM ENCONTRADO!")

# 2. Meias do Atlético-MG (visitante) - QUALQUER mando  
meias_vis = df_raw[df_raw['TIME'] == visitante]
print(f"\n⚪ Meias do {visitante} (TODOS os jogos):")
if len(meias_vis) > 0:
    print(meias_vis[['NOME', 'DATA', 'MANDO', 'ADVERSARIO', 'BASICA']].tail(window_n))
    print(f"   → Média BASICA: {meias_vis.groupby('MATCH_ID')['BASICA'].mean().tail(window_n).mean():.4f}")
else:
    print("  ❌ NENHUM ENCONTRADO!")

# 3. Meias dos ADVERSÁRIOS do Red Bull Bragantino
print(f"\n🟡 Meias dos ADVERSÁRIOS do {mandante}:")
adv_mand = df_raw[df_raw['ADVERSARIO'] == mandante]
print(f"   Total linhas: {len(adv_mand)}")
if len(adv_mand) > 0:
    print(adv_mand[['NOME', 'TIME', 'DATA', 'MANDO', 'BASICA']].head(10))
else:
    print("  ❌ NENHUM ENCONTRADO!")

# 4. Meias dos ADVERSÁRIOS do Atlético-MG
print(f"\n🟢 Meias dos ADVERSÁRIOS do {visitante}:")
adv_vis = df_raw[df_raw['ADVERSARIO'] == visitante]
print(f"   Total linhas: {len(adv_vis)}")
if len(adv_vis) > 0:
    print(adv_vis[['NOME', 'TIME', 'DATA', 'MANDO', 'BASICA']].head(10))
else:
    print("  ❌ NENHUM ENCONTRADO!")

print(f"\n{'='*80}\n")
