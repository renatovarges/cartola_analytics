
# Mapeamento de Arquivos e Pastas
INPUT_DIR = r"C:\Users\User\.gemini\antigravity\scratch\cartola_analytics\input"
EXCEL_FILE = "Scouts_Reorganizado.xlsx"

# Nomes das Abas do Excel
SHEET_POR_JOGO = "Por Jogo"
SHEET_SCOUTS = "Scouts"  # Aba secundária

# Colunas Essenciais - Aba "Por Jogo"
# Use UPPERCASE para as chaves internas, e os valores são as variações possíveis no Excel
COLS_POR_JOGO = {
    "NOME": ["NOME", "JOGADOR", "ATLETA", "Nome", "Nome2"],
    "TIME": ["TIME", "CLUBE", "EQUIPE", "Time"],
    "ADVERSARIO": ["ADVERSÁRIO", "ADVERSARIO", "OPONENTE", "Adversário"],
    "MANDO": ["MANDO", "LOCAL", "Mando", "Mand"],  # Esperado: CASA / FORA ou C / F ou Casa / Fora
    "DATA": ["DATA", "DATE", "DIA", "Data"],
    "POSICAO": ["POSICAO", "POSIÇÃO", "POS", "POSREAL", "Posreal"],
    "RODADA": ["RODADA", "R"],
    
    # Scouts - Meias/Ofensivos
    "G": ["G", "GOL", "GOLS"],
    "A": ["A", "ASS", "ASSISTENCIA"],
    "FF": ["FF", "FIN_FORA"],
    "FD": ["FD", "FIN_DEF"],
    "FT": ["FT", "FIN_TRAVE"],
    "BASICA": ["BÁSICA", "BASICA", "MEDIA_BASICA", "Básica", "Bás Tec"], # Média básica explícita
    "PONTOS": ["PTS", "PONTOS", "PONTUACAO", "Pts"],
    
    # Scouts - Defensivos
    "DS": ["DS", "DESARME"],
    "SG": ["SG", "SALDO_GOL"],
    "DE": ["DE", "DEFESA_DIFICIL"],
    "DP": ["DP", "DEFESA_PENALTI"],
    "GS": ["GS", "GOLS_SOFRIDOS"],
}

# IDs de Posição (String)
POS_IDS = {
    "GOLEIRO": ["1.0", "1"],
    "LATERAL": ["2.0", "2", "2.2", "2.6"],
    "ZAGUEIRO": ["3.0", "3"],
    "MEIA": ["4.0", "4", "4.0", "5.0"], # Atenção: 5.0 costuma ser atacante, mas vamos verificar se o usuário usa 4 e 5 para meias/atacantes.
    # O user disse que separa Meias de Volantes, mas por enquanto vamos pegar o codigo 4.
    # No print anterior vi 4.0 e 5.0. Cartola: 4=Meia, 5=Atacante.
    # Vou assumir 4.0 apenas para Meias iniciais.
    "MEIA_ONLY": ["4.0", "4"],
    "ATACANTE": ["5.0", "5"],
}

# Normalização de Nomes de Times
# Mapeia variações de nomes para o nome canônico usado na planilha
TEAM_ALIASES = {
    # Atlético Mineiro
    "ATLÉTICO": "ATLÉTICO-MG",
    "ATLETICO": "ATLÉTICO-MG",
    "CAM": "ATLÉTICO-MG",
    "GALO": "ATLÉTICO-MG",
    
    # Atlético Paranaense
    "ATHLETICO": "ATHLETICO-PR",
    "ATLÉTICO-PR": "ATHLETICO-PR",
    "CAP": "ATHLETICO-PR",
    
    # Atlético Goianiense  
    "ATLÉTICO-GO": "ATLÉTICO-GO",
    "ACG": "ATLÉTICO-GO",
    
    # Red Bull Bragantino
    "BRAGANTINO": "RED BULL BRAGANTINO",
    "RB BRAGANTINO": "RED BULL BRAGANTINO",
    
    # São Paulo
    "SAO PAULO": "SÃO PAULO",
    "SPFC": "SÃO PAULO",
    
    # Outros aliases comuns podem ser adicionados aqui
}
