import streamlit as st
import altair as alt
import numpy_financial as npf
from helpers import formato_moeda, tabela_price, money_input, percent_input


def render_taxa():
    st.header("Calcular Taxa")
    st.info("Informe Valor total, Entrada, nº de parcelas e o valor da parcela. O app encontra a taxa por período que gera essa parcela.")
    # Garantir chave de sessão para parcela (mantém valor entre reruns)
    if "parcela_informada" not in st.session_state:
        st.session_state["parcela_informada"] = 792

    # Inputs — cálculo automático
    c1, c2 = st.columns(2)
    valor_total = c1.number_input("Valor total (R$)", min_value=0.0, value=3519.0, format="%.2f", help="Preço total do bem/serviço")
    entrada = c2.number_input("Entrada (R$)", min_value=0.0, value=1000.0, format="%.2f", help="Valor pago à vista")
    c3, c4 = st.columns(2)
    num_parcelas = int(c3.number_input("Número de parcelas", min_value=1, value=5, step=1, help="Quantidade de parcelas (máx. 360 recomendadas)"))

    # Opção para tornar o campo 'parcela' editável; por padrão fica desabilitado e mantém o valor em session_state
    editar_parcela = c4.checkbox("Editar valor da parcela", value=False, key="editar_parcela_taxa", help="Ative para digitar manualmente o valor da parcela")

    # Antes de criar o number_input, atualizar o valor exibido caso não esteja em modo edição
    pv_est = max(0.0, float(valor_total) - float(entrada)) if (valor_total is not None and entrada is not None) else 0.0
    last_rate = st.session_state.get("last_rate_taxa", None)
    if not editar_parcela:
        # recalcular parcela exibida automaticamente: se tivermos uma taxa conhecida, usar ela, senão usar PV/n
        try:
            if last_rate is not None:
                auto_parcela = -npf.pmt(last_rate, int(num_parcelas), pv_est)
            else:
                auto_parcela = pv_est / max(1, int(num_parcelas))
        except Exception:
            auto_parcela = st.session_state.get("parcela_informada", 792)
        # atualizar session_state para refletir o novo valor mostrado
        st.session_state["parcela_informada_taxa"] = float(auto_parcela)

    # Usar widget com key para preservar o valor e evitar que mudanças em outros widgets o alterem
    parcela_informada = c4.number_input("Valor da parcela (R$)", min_value=0.0, value=float(st.session_state.get("parcela_informada_taxa", st.session_state.get("parcela_informada", 792))), format="%.2f", key="parcela_informada_taxa", disabled=not editar_parcela)

    # Validações reforçadas
    invalid = False
    if entrada is None or valor_total is None:
        invalid = True
        c1.error("Valores inválidos — verifique o formato (ex: 1.234,56).")
    else:
        if entrada > valor_total:
            invalid = True
            c2.error("Entrada não pode ser maior que o valor total.")

    if parcela_informada is None or parcela_informada <= 0:
        invalid = True
        c4.error("Valor da parcela deve ser maior que zero e em formato válido.")
    if num_parcelas > 360:
        invalid = True
        c3.error("Número de parcelas muito alto (máx. recomendado: 360).")

    if invalid:
        st.warning("Corrija os erros acima para ver o resultado.")
        return

    # Fazer o cálculo imediatamente
    st.session_state["parcela_informada"] = parcela_informada
    valor_financiado = max(0.0, valor_total - entrada)
    try:
        rate = npf.rate(num_parcelas, -parcela_informada, valor_financiado, fv=0)
        # checar taxa inválida extrema
        if rate is None or rate <= -0.999:
            st.error("Taxa calculada inválida ou muito negativa.")
            return

        taxa_mensal_percent = rate * 100
        taxa_anual_percent = (1 + rate) ** 12 - 1

        # Exibir métricas em colunas com breve explicação
        c_met1, c_met2 = st.columns(2)
        c_met1.metric("Taxa mensal (%)", f"{taxa_mensal_percent:.6f}%")
        c_met2.metric("Taxa anual equivalente (%)", f"{taxa_anual_percent * 100:.6f}%")

        parcela_calc = -npf.pmt(rate, num_parcelas, valor_financiado)
        st.write("Parcela calculada com a taxa encontrada:", formato_moeda(parcela_calc))

        df = tabela_price(rate, num_parcelas, valor_financiado)
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
