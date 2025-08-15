import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf


def formato_moeda(x):
    """Formata número como moeda BR (R$) usando vírgula como separador decimal.

    Retorna o próprio valor se não for numérico.
    """
    return f"R$ {x:,.2f}".replace(".", ",") if isinstance(x, (int, float, np.floating, np.integer)) else x


def tabela_price(rate, nper, pv):
    """Gera uma tabela de amortização PRICE como pandas.DataFrame.

    Campos: Período, Parcela, Juros, Amortização, Saldo Devedor
    """
    parcelas = []
    saldo = pv
    pmt = -npf.pmt(rate, nper, pv) if rate != 0 else pv / nper
    for periodo in range(1, nper + 1):
        juros = npf.ipmt(rate, periodo, nper, pv) if rate != 0 else 0.0
        amort = npf.ppmt(rate, periodo, nper, pv) if rate != 0 else -pmt
        saldo = saldo + amort
        parcelas.append({
            "Período": periodo,
            "Parcela": float(abs(pmt)),
            "Juros": float(abs(juros)),
            "Amortização": float(abs(amort)),
            "Saldo Devedor": float(abs(saldo)),
        })
    return pd.DataFrame(parcelas)


def _parse_number(value):
    """Tenta parsear uma entrada que pode conter vírgula como separador decimal."""
    if value is None:
        return None
    if isinstance(value, (int, float, np.floating, np.integer)):
        return float(value)
    # remover espaços e trocar vírgula por ponto
    try:
        s = str(value).strip().replace('.', '').replace(',', '.')
        return float(s)
    except Exception:
        return None



def _format_brl(value: float) -> str:
    # formata com separador de milhares '.' e decimal ',' (ex: 1.234,56)
    s = f"{value:,.2f}"
    # f-string usa ',' como separador de milhares e '.' como decimal -> trocar
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


def _parse_number_string(s: str) -> float:
    if s is None:
        raise ValueError("Valor vazio")
    s = str(s).strip()
    if s == "":
        raise ValueError("Valor vazio")
    # remover R$ se presente
    s = s.replace('R$', '').strip()
    # se contém vírgula, assumir formato BR: milhares com '.' e decimal com ','
    if ',' in s:
        # remover pontos de milhares
        s = s.replace('.', '')
        # trocar vírgula por ponto decimal
        s = s.replace(',', '.')
    # caso contrário, assume-se ponto como decimal
    # remover espaços
    s = s.replace(' ', '')
    try:
        return float(s)
    except Exception:
        raise ValueError(f"Não foi possível interpretar '{s}' como número")


def money_input(label: str, key: str, value: float = 0.0, help: str = None, disabled: bool = False):
    """Input textual para valores monetários que aceita formatos com vírgula ou ponto.

    Retorna float (ou lança ValueError). Usa `key` para o widget Streamlit.
    """
    default = _format_brl(value)
    raw = st.text_input(label, value=default, key=key, help=help, disabled=disabled)
    try:
        parsed = _parse_number_string(raw)
    except ValueError:
        # Em caso de erro, retornar None para posterior validação
        parsed = None
    return parsed


def percent_input(label: str, key: str, value: float = 0.0, help: str = None, disabled: bool = False):
    """Input textual para porcentagem; aceita vírgula ou ponto e retorna o valor em percent (ex: 2.5)."""
    # mostrar com vírgula
    default = f"{value:.6f}".replace('.', ',')
    raw = st.text_input(label, value=default, key=key, help=help, disabled=disabled)
    try:
        parsed = _parse_number_string(raw)
    except ValueError:
        parsed = None
    return parsed
