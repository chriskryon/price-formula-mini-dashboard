import numpy_financial as npf

# Dados do cartão (para confirmar a taxa)
valor_presente = 3519.00  # Valor à vista
num_parcelas_cartao = 5
valor_parcela_cartao = 792

# Calcular a taxa de juros mensal do cartão
# Fórmula utilizada (função npf.rate):
# npf.rate(nper, pmt, pv, fv=0)
# Onde:
#   nper = número de períodos (parcelas)
#   pmt = valor de cada pagamento (negativo, pois é saída de caixa)
#   pv = valor presente (valor à vista)
#   fv = valor futuro (zero, pois o saldo ao final é zero)
# A função retorna a taxa de juros por período que iguala o valor presente ao fluxo de pagamentos.
taxa_juros = npf.rate(num_parcelas_cartao, -valor_parcela_cartao, valor_presente, fv=0)
taxa_juros_percentual = taxa_juros * 100
print(f"Taxa de juros mensal (baseada no cartão): {taxa_juros_percentual:.4f}%")

# Cenário do boleto: entrada de R$ 1.000,00 e R$ 2.519,00 parcelados em 5x
entrada = 1000.00
valor_financiado = 3519.00 - entrada  # R$ 2.519,00
num_parcelas_boleto = 5


# Calcular o valor da parcela com a mesma taxa
# Fórmula utilizada (função npf.pmt):
# npf.pmt(rate, nper, pv, fv=0)
# Onde:
#   rate = taxa de juros por período
#   nper = número de períodos (parcelas)
#   pv = valor presente (valor financiado)
#   fv = valor futuro (zero)
# A função retorna o valor da parcela considerando o sistema PRICE (parcelas fixas).
valor_parcela_boleto = -npf.pmt(taxa_juros, num_parcelas_boleto, valor_financiado)
print(f"Valor da parcela no boleto (5x): R$ {valor_parcela_boleto:.2f}")

# Calcular juros totais
total_pago = valor_parcela_boleto * num_parcelas_boleto
juros_totais = total_pago - valor_financiado
print(f"Juros totais no boleto: R$ {juros_totais:.2f}")
print(f"Total a pagar (com entrada): R$ {entrada + total_pago:.2f}")

# Taxa de juros total (percentual sobre o valor financiado)
# Esta métrica é simplesmente a proporção dos juros pagos em relação ao
# valor financiado (juros_totais / valor_financiado). Não considera
# capitalização por período — é um rácio acumulado ao final do plano.
taxa_total_percentual = (juros_totais / valor_financiado) * 100 if valor_financiado != 0 else 0.0
print(
    f"Taxa total (juros / valor financiado): {taxa_total_percentual:.4f}%"
    + " — proporção dos juros pagos sobre o principal ao final do plano"
)

# Taxa efetiva acumulada ao longo dos n períodos: (1+rate)^n - 1
# A taxa efetiva acumulada traduz a taxa por período (taxa_juros) em uma
# taxa equivalente que leva em conta a capitalização composta durante N períodos.
# Use este valor para comparar custos quando a capitalização importa.
taxa_acumulada = (1 + taxa_juros) ** num_parcelas_boleto - 1
print(
    f"Taxa efetiva acumulada em {num_parcelas_boleto} períodos: {taxa_acumulada * 100:.4f}%"
    + " — equivalente considerando capitalização: (1+rate)^n - 1"
)

# Tabela PRICE para as 5 parcelas
saldo_devedor = valor_financiado
print("\nTabela PRICE - 5 Parcelas:")
print("Período | Parcela    | Juros     | Amortização | Saldo Devedor")
print("-" * 60)

for periodo in range(1, num_parcelas_boleto + 1):
    juros = npf.ipmt(taxa_juros, periodo, num_parcelas_boleto, valor_financiado)
    amortizacao = npf.ppmt(taxa_juros, periodo, num_parcelas_boleto, valor_financiado)
    saldo_devedor += amortizacao
    print(f"{periodo:7d} | {abs(valor_parcela_boleto):9.2f} | {abs(juros):9.2f} | {abs(amortizacao):9.2f} | {abs(saldo_devedor):13.2f}")