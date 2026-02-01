import unicodedata

def normalize_string(s):
    """Remove acentos e caracteres especiais de forma nativa."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def get_team_filename(team_name):
    """
    Converte o nome do time para o padrão de arquivo na pasta assets/teams.
    Ex: "São Paulo" -> "sao_paulo.png"
    """
    if not team_name:
        return "default.png"
        
    # Normalização: lowercase, sem acentos
    s = str(team_name).lower().strip()
    s = normalize_string(s)
    
    # Espaços e hífens viram underline
    clean_name = s.replace(" ", "_")
    clean_name = clean_name.replace("-", "_")
    
    # Tratamentos Especiais (Aliases comuns baseados nos arquivos vistos)
    if clean_name == "athletico": return "athletico_pr.png"
    if clean_name == "atletico": return "atletico_mg.png" 
    if clean_name == "atletico_go": return "atletico_go.png"
    
    return f"{clean_name}.png"
