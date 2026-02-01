import re

def parse_rounds_file(file_path):
    """
    Lê o arquivo de rodadas txt e retorna um dicionário:
    {
        1: [("FLUMINENSE", "GRÊMIO"), ("BOTAFOGO", "CRUZEIRO"), ...],
        2: ...
    }
    """
    rounds = {}
    current_round = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Identificar cabeçalho da rodada (ex: "Rodada 1 (...)")
            match_round = re.match(r"^Rodada\s+(\d+)", line, re.IGNORECASE)
            if match_round:
                current_round = int(match_round.group(1))
                rounds[current_round] = []
                continue
                
            # Identificar confronto (ex: "Time A x Time B")
            if " x " in line.lower() and current_round:
                parts = line.split(" x " if " x " in line else " X ")
                if len(parts) == 2:
                    home = parts[0].strip().upper()
                    away = parts[1].strip().upper()
                    rounds[current_round].append((home, away))
                    
    return rounds

def get_confrontos(rounds_data, rodada_alvo):
    return rounds_data.get(rodada_alvo, [])
