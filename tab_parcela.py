import streamlit as st
import altair as alt
import pandas as pd
import numpy_financial as npf
from helpers import formato_moeda, tabela_price, money_input, percent_input


def render_parcela():
    st.header("Calcular Parcela")
    st.info("Informe Valor total, Entrada, número de parcelas e a taxa (mensal ou anual). Retorna a parcela fixa (PRICE), juros totais e tabela de amortização.")
    # Inputs — cálculo automático (sem formulário)
    c1, c2 = st.columns(2)
    valor_total = money_input("Valor total (R$)", key="par_valor_total", value=3519.0, help="Preço total do bem/serviço")
    entrada = money_input("Entrada (R$)", key="par_entrada", value=1000.0, help="Valor pago à vista")
    c3, c4 = st.columns(2)
    num_parcelas = int(c3.number_input("Número de parcelas", min_value=1, value=5, step=1, help="Quantidade de parcelas (máx. 360 recomendadas)"))
    taxa_input_tipo = c4.selectbox("Taxa informada como", ["Mensal (%)", "Anual (%)"], index=0)
    taxa_percent = percent_input("Taxa por período (%)", key="par_taxa", value=4.069200, help="Informe em % por período (ex: 2,5)")

    # Validações reforçadas
    invalid = False
    if valor_total is None or entrada is None:
        invalid = True
        c1.error("Valores inválidos — verifique o formato (ex: 1.234,56).")
    else:
        if entrada > valor_total:
            invalid = True
            c2.error("Entrada não pode ser maior que o valor total.")
    if taxa_percent is None:
        invalid = True
        c4.error("Taxa inválida — verifique o formato.")
    if num_parcelas > 360:
        invalid = True
        c3.error("Número de parcelas muito alto (máx. recomendado: 360).")

    if invalid:
        st.warning("Corrija os erros acima para ver o resultado.")
        return

    # Cálculo e exibição imediata
    valor_financiado = max(0.0, valor_total - entrada)
    rate = taxa_percent / 100.0
    if taxa_input_tipo == "Anual (%)":
        rate = rate / 12.0

    if rate == 0:
        parcela = valor_financiado / num_parcelas
    else:
        parcela = -npf.pmt(rate, num_parcelas, valor_financiado)

    total_pago = parcela * num_parcelas
    juros_totais = total_pago - valor_financiado

    # --- Métricas de resultado (organizadas) ---
    m1, m2 = st.columns(2)
    m1.metric("Valor financiado (PV)", formato_moeda(valor_financiado))
    m1.metric("Parcela (período)", formato_moeda(parcela))
    m2.metric("Total pago (sem entrada)", formato_moeda(total_pago))
    m2.metric("Juros totais", formato_moeda(juros_totais))

    # Taxas: percentual total e efetiva acumulada
    if valor_financiado > 0:
        taxa_total_percentual = (juros_totais / valor_financiado) * 100.0
    else:
        taxa_total_percentual = 0.0

    if rate <= -1:
        taxa_acumulada = None
    elif rate == 0:
        taxa_acumulada = 0.0
    else:
        taxa_acumulada = (1.0 + rate) ** num_parcelas - 1.0

    t1, t2 = st.columns(2)
    t1.metric("Taxa total (sobre o valor financiado)", f"{taxa_total_percentual:.2f} %")
    if taxa_acumulada is None:
        t2.info("Taxa efetiva acumulada: inválida para a taxa informada (<= -100%).")
        taxa_acumulada_val = 0.0
    else:
        t2.metric("Taxa efetiva acumulada", f"{taxa_acumulada*100:.2f} %")
        taxa_acumulada_val = taxa_acumulada * 100.0

    # --- Gráfico: comparação Taxa total x Taxa efetiva acumulada ---
    try:
        chart_df = pd.DataFrame({
            "Métrica": ["Taxa total", "Taxa efetiva acumulada"],
            "Valor (%)": [round(taxa_total_percentual, 6), round(taxa_acumulada_val, 6)]
        })
        # garantir ordem e cores fixas
        color_scale = alt.Scale(domain=["Taxa total", "Taxa efetiva acumulada"], range=["#d62728", "#1f77b4"])
        bar = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('Métrica:N', title='Métrica'),
            y=alt.Y('Valor (%):Q', title='Percentual (%)', axis=alt.Axis(format='.2f')),
            color=alt.Color('Métrica:N', scale=color_scale, legend=None),
            tooltip=[alt.Tooltip('Métrica:N'), alt.Tooltip('Valor (%):Q', format='.2f')]
        )
        # adicionar rótulos com o valor em cima das barras
        text = bar.mark_text(dy=-8, color='black').encode(text=alt.Text('Valor (%):Q', format='.2f'))
        # st.subheader("Comparação: Taxa total vs Taxa efetiva acumulada")
        # st.altair_chart((bar + text).configure_view(strokeWidth=0), use_container_width=True)
    except Exception:
        # fallback silencioso se algo falhar na construção do gráfico
        pass

    # --- Gráfico: evolução da taxa efetiva acumulada por período ---
    if rate is None or rate <= -1:
        st.info("Não é possível gerar o gráfico de evolução da taxa efetiva para a taxa informada.")
    else:
        acum = [((1.0 + rate) ** k - 1.0) * 100.0 for k in range(1, num_parcelas + 1)]
        df_acc = pd.DataFrame({"Período": list(range(1, num_parcelas + 1)), "Acumulado (%)": acum})
        line = alt.Chart(df_acc).mark_line(point=True).encode(
            x=alt.X('Período:O', title='Período'),
            y=alt.Y('Acumulado (%):Q', title='Acumulado (%)', axis=alt.Axis(format='.2f')),
            tooltip=[alt.Tooltip('Período:O'), alt.Tooltip('Acumulado (%):Q', format='.2f')]
        )
        # st.subheader("Evolução: Taxa efetiva acumulada ao longo dos períodos")
        # st.altair_chart(line.configure_view(strokeWidth=0), use_container_width=True)

    # Tabela de amortização (PRICE)
    df = tabela_price(rate, num_parcelas, valor_financiado)
    df_display = df.copy()
    for c in ["Parcela", "Juros", "Amortização", "Saldo Devedor"]:
        df_display[c] = df_display[c].apply(lambda x: f"R$ {x:,.2f}")
    st.subheader("Tabela de Amortização (PRICE)")
    st.table(df_display)

    # Gráficos
    st.subheader("Saldo Devedor")
    chart_balance = alt.Chart(df).mark_line(point=True).encode(x=alt.X('Período:O'), y=alt.Y('Saldo Devedor:Q'))
    st.altair_chart(chart_balance, use_container_width=True)

    st.subheader("Composição: Juros x Amortização")
    comp_long = df.melt(id_vars='Período', value_vars=['Juros', 'Amortização'], var_name='Tipo', value_name='Valor')
    chart_comp = alt.Chart(comp_long).mark_area(opacity=0.6).encode(
        x=alt.X('Período:O'), y=alt.Y('Valor:Q', stack='zero'),
        color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Juros','Amortização'], range=['#d62728','#1f77b4']))
    )
    st.altair_chart(chart_comp, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar tabela (CSV)", csv, file_name='tabela_parcela.csv', mime='text/csv')
