"""
Trava a Regra de Ouro, que existia no papel e nunca rodou.

O erro que estes testes impedem de voltar (05/out/2026): o material da rodada
29 saiu errado porque o app tinha uma "Data de Corte" com 18/09 cravado no
codigo, e o corte automatico que deveria substitui-la procurava uma coluna
chamada RODADA quando a planilha traz "Rodada PADV". A busca levantava
KeyError, um `except: pass` engolia, e o sistema caia na data manual em
silencio, descartando a rodada 28 inteira.
"""
import pandas as pd
import pytest
from src.engine import CartolaEngine


def _motor_de_mentira():
    """Motor com uma base minima, sem precisar de planilha no disco."""
    eng = object.__new__(CartolaEngine)
    eng.df_pj = pd.DataFrame(
        {
            "TIME": ["GRÊMIO", "PALMEIRAS", "BAHIA"],
            "ADVERSARIO": ["PALMEIRAS", "GRÊMIO", "ATHLETICO-PR"],
            "MANDO": ["CASA", "FORA", "FORA"],
            "DATA": pd.to_datetime(["2026-09-21", "2026-09-21", "2026-09-21"]),
            "Rodada PADV": [28, 28, 28],
        }
    )
    eng.df_pj["RODADA"] = eng.df_pj["Rodada PADV"]
    return eng


def test_rodada_passada_corta_na_data_real_do_jogo():
    eng = _motor_de_mentira()
    corte = eng._data_de_corte("GRÊMIO", "PALMEIRAS", 28, pd.to_datetime("2026-09-18"))
    assert corte == pd.Timestamp("2026-09-21")


def test_rodada_futura_nao_corta_nada():
    """O caso que quebrou a tabela: jogo que ainda nao aconteceu nao esta na
    base, e manter a data manual descartava a ultima rodada disputada."""
    eng = _motor_de_mentira()
    assert eng._data_de_corte("PALMEIRAS", "BAHIA", 29, pd.to_datetime("2026-09-18")) is None


def test_sem_rodada_a_data_manual_ainda_vale():
    eng = _motor_de_mentira()
    manual = pd.to_datetime("2026-09-18")
    assert eng._data_de_corte("GRÊMIO", "PALMEIRAS", None, manual) == manual


def test_coluna_rodada_e_reconhecida_mesmo_com_outro_nome():
    """A planilha chama de 'Rodada PADV'. Se a normalizacao sumir, o corte
    automatico volta a falhar calado, que foi exatamente o defeito."""
    eng = object.__new__(CartolaEngine)
    df = pd.DataFrame(
        {
            "TIME": ["GRÊMIO"],
            "ADVERSARIO": ["PALMEIRAS"],
            "MANDO": ["CASA"],
            "DATA": pd.to_datetime(["2026-09-21"]),
            "Rodada PADV": [28],
        }
    )
    df["MATCH_ID"] = ["2026-09-21|GRÊMIO|PALMEIRAS"]
    eng.df_pj = df
    CartolaEngine._prepare_base_data.__wrapped__(eng) if hasattr(
        CartolaEngine._prepare_base_data, "__wrapped__"
    ) else CartolaEngine._prepare_base_data(eng)
    assert "RODADA" in eng.df_pj.columns
    assert eng._data_de_corte("GRÊMIO", "PALMEIRAS", 28, None) == pd.Timestamp("2026-09-21")


def test_janela_nao_escorrega_quando_o_jogo_nao_tem_meia():
    """
    Jogo em que nenhum meia classificado entrou vale ZERO, nao vale 'nao
    aconteceu'. Medido na base real: o Gremio em casa usava um jogo de 10/08
    como um dos 'ultimos 3' porque o de 21/09 tinha sumido.
    """
    eng = object.__new__(CartolaEngine)
    universo = pd.DataFrame(
        {
            "TIME": ["GRÊMIO"] * 3,
            "MANDO": ["CASA"] * 3,
            "MATCH_ID": ["j1", "j2", "j3"],
            "DATA": pd.to_datetime(["2026-08-10", "2026-09-01", "2026-09-21"]),
            "G": [0, 0, 0], "A": [0, 0, 0], "PG": [0, 0, 0],
            "CHUTES": [0, 0, 0], "AF": [0, 0, 0], "DE": [0, 0, 0], "BASICA": [1.0, 1.0, 1.0],
        }
    )
    # o recorte de meias nao tem o jogo mais recente (so volantes entraram nele)
    so_meias = universo[universo["MATCH_ID"] != "j3"].copy()
    so_meias.loc[so_meias["MATCH_ID"] == "j1", "G"] = 5  # gol antigo que nao pode entrar

    com = eng.get_aggregated_stats(so_meias, 2, time_filter="GRÊMIO", mando_filter="CASA", df_universo=universo)
    assert com["G"] == 0, "a janela pegou um jogo velho que ja devia ter saido"

    sem = eng.get_aggregated_stats(so_meias, 2, time_filter="GRÊMIO", mando_filter="CASA")
    assert sem["G"] == 5, "sem o universo, o defeito antigo continua reproduzivel"
