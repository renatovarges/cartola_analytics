"""
Função para carregar classificação de Meias vs Volantes
"""
import pandas as pd
import os

def load_meias_volantes_classification(csv_path=None):
    """
    Carrega classificação de meias/volantes do CSV.
    Retorna dicionário: {JOGADOR: "MEIA" ou "VOLANTE"}
    """
    if csv_path is None:
        # Path padrão
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
    
    # Normalizar nomes de colunas para UPPERCASE para evitar problemas
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Identificar a coluna de nome do jogador (pode ser NOME ou JOGADOR)
    nome_col = None
    for candidate in ["NOME", "JOGADOR", "ATLETA", "PLAYER"]:
        if candidate in df.columns:
            nome_col = candidate
            break
    
    if nome_col is None:
        print(f"AVISO: Nenhuma coluna de nome encontrada no CSV. Colunas: {list(df.columns)}")
        return {}
    
    # Criar dicionário JOGADOR -> CLASSIFICACAO
    classificacao_dict = {}
    for _, row in df.iterrows():
        jogador = str(row[nome_col]).strip().upper()
        classe = row.get('CLASSIFICACAO', row.get('CLASSE', None))
        if pd.notna(classe):
            classificacao_dict[jogador] = str(classe).strip().upper()
    
    print(f"✅ Classificação carregada: {len(classificacao_dict)} jogadores")
    print(f"   - Meias: {list(classificacao_dict.values()).count('MEIA')}")
    print(f"   - Volantes: {list(classificacao_dict.values()).count('VOLANTE')}")
    
    return classificacao_dict
