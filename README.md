# Calculadora de Juros e Valor Presente (Streamlit)

Pequena aplicação Streamlit para calcular parcelas, taxas e valor presente usando o sistema PRICE.

Requisitos

- Python 3.8+
- Windows PowerShell (comandos abaixo são para PowerShell)

Instalação e execução (PowerShell)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip; pip install -r requirements.txt
streamlit run streamlit_app.py
```

Uso

- Ajuste `Valor total`, `Entrada`, `Número de parcelas` e escolha o modo (calcular parcela, taxa ou valor presente) na barra lateral.
- A tabela de amortização e métricas são atualizadas automaticamente.

