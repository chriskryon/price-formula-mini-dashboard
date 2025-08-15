import streamlit as st
import altair as alt
import numpy_financial as npf
from helpers import formato_moeda, tabela_price, money_input, percent_input


def render_pv():
    st.header("Calcular Valor Presente (PV)")
    st.info("Informe nº de parcelas, taxa (mensal ou anual) e o valor da parcela. O app calcula o PV no sistema PRICE.")

    # Inputs — cálculo automático
    c1, c2 = st.columns(2)
    num_parcelas = int(c1.number_input("Número de parcelas", min_value=1, value=5, step=1, help="Quantidade de parcelas (máx. 360 recomendadas)"))
    taxa_input_tipo = c1.selectbox("Taxa informada como", ["Mensal (%)", "Anual (%)"], index=0)
    taxa_percent = percent_input("Taxa por período (%)", key="pv_taxa", value=2.0, help="Informe em % por período (ex: 2,5)")
    parcela_futura = money_input("Valor da parcela (R$)", key="pv_parcela", value=324.92, help="Valor da parcela futura")

    invalid = False
    if taxa_percent is None:
        invalid = True
        c1.error("Taxa inválida — verifique o formato.")
    if parcela_futura is None or parcela_futura <= 0:
        invalid = True
        c2.error("Valor da parcela deve ser maior que zero e em formato válido.")
    if num_parcelas > 360:
        invalid = True
        c1.error("Número de parcelas muito alto (máx. recomendado: 360).")

    if invalid:
        st.warning("Corrija os erros acima para ver o resultado.")
        return

    rate = taxa_percent / 100.0
    if taxa_input_tipo == "Anual (%)":
        rate = rate / 12.0

    try:
        pv = -npf.pv(rate, num_parcelas, parcela_futura, fv=0)
        col_left, col_right = st.columns([2, 1])
        col_left.metric("Valor presente (PV)", formato_moeda(pv))
        col_right.caption("PV calculado no sistema PRICE considerando parcelas fixas.")

        df = tabela_price(rate, num_parcelas, pv)
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
