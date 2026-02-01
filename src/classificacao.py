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
    
    # Criar dicionário JOGADOR -> CLASSIFICACAO
    # Normalizar nomes para uppercase
    classificacao_dict = {}
    for _, row in df.iterrows():
        jogador = str(row['JOGADOR']).strip().upper()
        classe = row['CLASSIFICACAO']
        if pd.notna(classe):
            classificacao_dict[jogador] = classe
    
    print(f"✅ Classificação carregada: {len(classificacao_dict)} jogadores")
    print(f"   - Meias: {list(classificacao_dict.values()).count('MEIA')}")
    print(f"   - Volantes: {list(classificacao_dict.values()).count('VOLANTE')}")
    
    return classificacao_dict
