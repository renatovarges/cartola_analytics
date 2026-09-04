"""Regras centralizadas de destaque estatístico.

Cor representa destaque real, nunca uma cota visual. Os cortes-base foram
calibrados para 3 jogos pelo mando. Métricas de soma escalam com a janela;
médias permanecem absolutas.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Thresholds:
    light: float
    medium: float
    dark: float
    is_average: bool = False

    def for_window(self, window_n: int) -> "Thresholds":
        if self.is_average or window_n == 3:
            return self
        factor = max(float(window_n), 1.0) / 3.0
        return Thresholds(
            light=math.ceil(self.light * factor),
            medium=math.ceil(self.medium * factor),
            dark=math.ceil(self.dark * factor),
            is_average=False,
        )


# Corte claro já representa dado relevante; mediano continua branco.
POSITION_THRESHOLDS = {
    "ATACANTES": {
        # 13 foi comum demais e quase não separou o jogo seguinte. 17+ separou.
        "CHUTES": Thresholds(17, 20, 23),
        "PG": Thresholds(3, 5, 7),
        # Gol é o principal retorno do atacante; G+A recebe escala própria.
        "BASICA": Thresholds(2.6, 3.0, 3.5, True),
    },
    "MEIAS": {
        "AF": Thresholds(8, 9, 12),
        "CHUTES": Thresholds(7, 9, 12),
        "PG": Thresholds(2, 3, 5),
        "BASICA": Thresholds(2.4, 2.9, 3.3, True),
    },
    "VOLANTES": {
        "DE": Thresholds(11, 14, 17),
        # Participação ofensiva é bônus raro, nunca o eixo da posição.
        "PG": Thresholds(2, 3, 4),
        # Somente a antiga faixa alta mostrou persistência clara.
        "BASICA": Thresholds(3.4, 4.0, 4.8, True),
    },
    "LATERAIS": {
        "DE": Thresholds(6, 8, 10),
        "PG": Thresholds(1, 2, 3),
        "BASICA": Thresholds(3.1, 3.7, 4.2, True),
    },
    "ZAGUEIROS": {
        "DE": Thresholds(9, 11, 14),
        "CHUTES": Thresholds(3, 4, 5),
        "BASICA": Thresholds(2.7, 3.1, 3.5, True),
        # Os demais números continuam visíveis, mas falharam como sinal agregado.
        # Finalizações voltarão a ser avaliadas na concentração por jogador.
    },
}


def metric_from_column(col_name: str) -> str | None:
    name = str(col_name).upper()
    if "BAS" in name:
        return "BASICA"
    if "PTS" in name or "PONTOS" in name:
        return "PONTOS"
    if "CHUTES" in name:
        return "CHUTES"
    if "_PG" in name or name.endswith("PG"):
        return "PG"
    if "_AF" in name or name.endswith("AF"):
        return "AF"
    if "_DE" in name or name.endswith("DE"):
        return "DE"
    return None


def get_thresholds(position: str, col_name: str, window_n: int) -> Thresholds | None:
    metric = metric_from_column(col_name)
    base = POSITION_THRESHOLDS.get(str(position).upper(), {}).get(metric)
    return base.for_window(window_n) if base else None


def classify(position: str, col_name: str, value, window_n: int) -> str | None:
    """Retorna dark/medium/light ou None. Não limita quantidade de destaques."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    thresholds = get_thresholds(position, col_name, window_n)
    if thresholds is None:
        return None
    if thresholds.is_average:
        number = round(number, 1)
    if number >= thresholds.dark:
        return "dark"
    if number >= thresholds.medium:
        return "medium"
    if number >= thresholds.light:
        return "light"
    return None


def classify_cell(position: str, col_name: str, value, row, window_n: int) -> str | None:
    """Classifica cada célula pelo seu próprio valor.

    Produção e concessão são informações válidas separadamente. A combinação
    entre elas é feita na leitura do confronto, sem esconder uma célula forte.
    """
    return classify(position, col_name, value, window_n)


_LEVEL_RANK = {None: 0, "light": 1, "medium": 2, "dark": 3}


def caption_qualifies(position: str, metric: str, own_value, conceded_value,
                      window_n: int, support: dict | None = None) -> bool:
    """Decide a entrada na legenda usando exatamente a régua das cores.

    A legenda é mais seletiva que a tabela: entra um destaque próprio forte
    (faixa escura) ou um cruzamento em que produção e concessão alcançam a
    faixa média. Exceções de hierarquia ficam explícitas aqui, nunca espalhadas
    nos geradores de texto.
    """
    pos, scout = str(position).upper(), str(metric).upper()
    own = _LEVEL_RANK[classify(pos, scout, own_value, window_n)]
    conceded = _LEVEL_RANK[classify(pos, scout, conceded_value, window_n)]
    support = support or {}

    if pos == "ATACANTES" and scout == "PG":
        shots = _LEVEL_RANK[classify(pos, "CHUTES", support.get("CHUTES", 0), window_n)]
        return own >= 2 or (own >= 1 and shots >= 2)
    if pos == "ATACANTES" and scout == "CHUTES":
        return own >= 2 or (own >= 1 and conceded >= 1)

    # Em todas as demais leituras validadas, a regra operacional é a mesma:
    # faixa escura própria OU faixa média confirmada pelos dois lados.
    return own >= 3 or (own >= 2 and conceded >= 2)
