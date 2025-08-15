import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import numpy_financial as npf

# modular tabs
from tab_parcela import render_parcela
from tab_taxa import render_taxa
from tab_pv import render_pv

# helpers
import helpers


st.set_page_config(page_title="Calculadora de Juros e Valor Presente", layout="centered")
st.title("Calculadora interativa: Valor Presente, Parcelas e Taxa")

st.markdown(
    "Insira os valores abaixo. Escolha a aba correspondente ao cálculo que deseja realizar; cada aba mostra apenas os campos necessários."
)

# Criar abas (tabs) — uma aba por modo
tabs = st.tabs(["Calcular Parcela", "Calcular Taxa", "Calcular Valor Presente"])

# Aba: Calcular Parcela (usa o módulo tab_parcela.render_parcela)
with tabs[0]:
    # Chamamos a função modularizada que já contém o formulário e as métricas
    render_parcela()

# Aba: Calcular Taxa
with tabs[1]:
    st.header("Calcular Taxa")
    st.info("Informe Valor total, Entrada, nº de parcelas e o valor da parcela. O app encontra a taxa por período que gera essa parcela.")
    with st.form("form_taxa"):
        c1, c2 = st.columns(2)
        valor_total = c1.number_input("Valor total (R$)", min_value=0.0, value=3519.0, format="%.2f")
        entrada = c2.number_input("Entrada (R$)", min_value=0.0, value=1000.0, format="%.2f")
        c3, c4 = st.columns(2)
        num_parcelas = int(c3.number_input("Número de parcelas", min_value=1, value=12, step=1))
        parcela_informada = c4.number_input("Valor da parcela (R$)", min_value=0.0, value=324.92, format="%.2f")

        invalid = entrada > valor_total
        if invalid:
            c2.error("Entrada não pode ser maior que o valor total.")

        submitted = st.form_submit_button("Calcular Taxa", disabled=invalid)

    if submitted:
        valor_financiado = max(0.0, valor_total - entrada)
        try:
            rate = npf.rate(num_parcelas, -parcela_informada, valor_financiado, fv=0)
            taxa_mensal_percent = rate * 100
            taxa_anual_percent = (1 + rate) ** 12 - 1

            st.metric("Taxa mensal (%)", f"{taxa_mensal_percent:.6f}%")
            st.metric("Taxa anual equivalente (%)", f"{taxa_anual_percent * 100:.6f}%")

            parcela_calc = -npf.pmt(rate, num_parcelas, valor_financiado)
            st.write("Parcela calculada com a taxa encontrada:", helpers.formato_moeda(parcela_calc))

            df = helpers.tabela_price(rate, num_parcelas, valor_financiado)
            df_display = df.copy()
            for c in ["Parcela", "Juros", "Amortização", "Saldo Devedor"]:
                df_display[c] = df_display[c].apply(lambda x: f"R$ {x:,.2f}")
            st.subheader("Tabela de Amortização (PRICE)")
            st.table(df_display)

            st.subheader("Saldo Devedor")
            chart_balance = alt.Chart(df).mark_line(point=True).encode(x=alt.X('Período:O'), y=alt.Y('Saldo Devedor:Q'))
            st.altair_chart(chart_balance, use_container_width=True)

            st.subheader("Composição: Juros x Amortização")
            comp_long = df.melt(id_vars='Período', value_vars=['Juros', 'Amortização'], var_name='Tipo', value_name='Valor')
            chart_comp = alt.Chart(comp_long).mark_area(opacity=0.6).encode(x=alt.X('Período:O'), y=alt.Y('Valor:Q', stack='zero'), color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Juros','Amortização'], range=['#d62728','#1f77b4'])))
            st.altair_chart(chart_comp, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar tabela (CSV)", csv, file_name='tabela_taxa.csv', mime='text/csv')
        except Exception as e:
            st.error(f"Não foi possível calcular a taxa: {e}")

# Aba: Calcular Valor Presente
with tabs[2]:
    st.header("Calcular Valor Presente (PV)")
    st.info("Informe nº de parcelas, taxa (mensal ou anual) e o valor da parcela. O app calcula o PV no sistema PRICE.")
    with st.form("form_pv"):
        c1, c2 = st.columns(2)
        num_parcelas = int(c1.number_input("Número de parcelas", min_value=1, value=5, step=1))
        taxa_input_tipo = c1.selectbox("Taxa informada como", ["Mensal (%)", "Anual (%)"], index=0)
        taxa_percent = c2.number_input("Taxa por período (%)", value=2.0, format="%.6f")
        parcela_futura = c2.number_input("Valor da parcela (R$)", min_value=0.0, value=324.92, format="%.2f")

        submitted = st.form_submit_button("Calcular PV")

    if submitted:
        rate = taxa_percent / 100.0
        if taxa_input_tipo == "Anual (%)":
            rate = rate / 12.0

        try:
            pv = -npf.pv(rate, num_parcelas, parcela_futura, fv=0)
            st.metric("Valor presente (PV)", helpers.formato_moeda(pv))

            df = helpers.tabela_price(rate, num_parcelas, pv)
            df_display = df.copy()
            for c in ["Parcela", "Juros", "Amortização", "Saldo Devedor"]:
                df_display[c] = df_display[c].apply(lambda x: f"R$ {x:,.2f}")
            st.subheader("Tabela de Amortização (PRICE)")
            st.table(df_display)

            st.subheader("Saldo Devedor")
            chart_balance = alt.Chart(df).mark_line(point=True).encode(x=alt.X('Período:O'), y=alt.Y('Saldo Devedor:Q'))
            st.altair_chart(chart_balance, use_container_width=True)

            st.subheader("Composição: Juros x Amortização")
            comp_long = df.melt(id_vars='Período', value_vars=['Juros', 'Amortização'], var_name='Tipo', value_name='Valor')
            chart_comp = alt.Chart(comp_long).mark_area(opacity=0.6).encode(x=alt.X('Período:O'), y=alt.Y('Valor:Q', stack='zero'), color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Juros','Amortização'], range=['#d62728','#1f77b4'])))
            st.altair_chart(chart_comp, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar tabela (CSV)", csv, file_name='tabela_pv.csv', mime='text/csv')
        except Exception as e:
            st.error(f"Erro no cálculo do valor presente: {e}")
