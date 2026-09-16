"""
Função para carregar classificação de Meias vs Volantes.
Inclui normalização de acentos para matching robusto entre
nomes do CSV e nomes da planilha do Gato Mestre.
"""
import pandas as pd
import os
import unicodedata


def _normalize_name(name):
    """Remove acentos e normaliza para matching robusto."""
    name = str(name).strip().upper()
    nfkd = unicodedata.normalize('NFKD', name)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_team(name):
    team = _normalize_name(name)
    return {
        "INTER": "INTERNACIONAL",
        "RB BRAGANTINO": "RED BULL BRAGANTINO",
    }.get(team, team)


def load_meias_volantes_classification(csv_path=None):
    """
    Carrega classificação de meias/volantes do CSV.
    Retorna dicionário indexado por (TIME, JOGADOR), ambos normalizados.
    Assim jogadores homônimos e transferências preservam a função por clube.
    """
    if csv_path is None:
        csv_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "input", 
            "classificacao_meias_volantes.csv"
        )
    
    if not os.path.exists(csv_path):
        print(f"AVISO: Arquivo de classificação não encontrado: {csv_path}")
        return {}
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Normalizar nomes de colunas para UPPERCASE
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Identificar a coluna de nome do jogador
    nome_col = None
    for candidate in ["JOGADOR", "NOME", "ATLETA", "PLAYER"]:
        if candidate in df.columns:
            nome_col = candidate
            break
    
    if nome_col is None:
        print(f"AVISO: Nenhuma coluna de nome encontrada no CSV. Colunas: {list(df.columns)}")
        return {}
    
    if "TIME" not in df.columns:
        raise ValueError("Arquivo de classificação sem coluna TIME")

    classificacao_dict = {}
    meias_count = 0
    volantes_count = 0
    
    for _, row in df.iterrows():
        jogador = str(row[nome_col]).strip().upper()
        classe = row.get('CLASSIFICACAO', row.get('CLASSE', None))
        
        if pd.notna(classe):
            classe_str = str(classe).strip().upper()
            
            key = (_normalize_team(row["TIME"]), _normalize_name(jogador))
            if key in classificacao_dict and classificacao_dict[key] != classe_str:
                raise ValueError(f"Classificação conflitante para {row['TIME']} / {jogador}")
            classificacao_dict[key] = classe_str
            
            if classe_str == "MEIA":
                meias_count += 1
            elif classe_str == "VOLANTE":
                volantes_count += 1
    
    print(f"✅ Classificação carregada: {meias_count + volantes_count} jogadores")
    print(f"   - Meias: {meias_count}")
    print(f"   - Volantes: {volantes_count}")
    
    return classificacao_dict
