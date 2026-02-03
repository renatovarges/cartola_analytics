import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import CartolaEngine
from src import config

file_path = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input\Scouts_Reorganizado.xlsx"
engine = CartolaEngine(file_path)

print("=== VERIFICAÇÃO DE NORMALIZAÇÃO DE NOMES ===\n")

# Verificar se nomes na coluna ADVERSARIO batem com TEAM_ALIASES
unique_advs = engine.df_pj["ADVERSARIO"].unique()
print(f"Total de adversários únicos: {len(unique_advs)}")

aliases_values = set(config.TEAM_ALIASES.values())

inconsistencies = []
for adv in unique_advs:
    # Se adv não está nos aliases_values (e configs usam aliases), pode ser problema?
    # Mas config.TEAM_ALIASES é Dict[De -> Para]. Values são os nomes oficiais.
    # Vamos ver se engine.df_pj já normaliza TIME e ADVERSARIO no init.
    pass

print("Amostra ADVERSARIO:", unique_advs[:10])
print("Amostra TIME:", engine.df_pj["TIME"].unique()[:10])

# Verificar filtro cruzado
matches = engine.df_pj[engine.df_pj["TIME"] == "CRUZEIRO"]
if not matches.empty:
    advs = matches["ADVERSARIO"].unique()
    print(f"\nAdversários do CRUZEIRO na base: {advs}")
    
    # Teste reverso
    matches_rev = engine.df_pj[engine.df_pj["ADVERSARIO"] == "CRUZEIRO"]
    times_rev = matches_rev["TIME"].unique()
    print(f"Times que enfrentaram CRUZEIRO (pela coluna ADVERSARIO): {times_rev}")
