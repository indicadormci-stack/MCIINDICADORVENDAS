
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- Config ---
st.set_page_config(page_title="Vendas por Cliente", layout="wide")

# --- Carrega dados ---
@st.cache_data
def load_data(path="Banco de Dados Vendas.xlsx"):
    df = pd.read_excel(path, sheet_name="Banco de Dados")
    # assegurar tipos
    df = df.rename(columns=lambda x: x.strip())
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Ano"] = df["Ano"].astype(str)
    return df

df = load_data()

st.title("Análise de Vendas — Top 10 Clientes")
st.markdown("Interface dinâmica para visualizar vendas por cliente e por ano. Filtre por ano ou selecione **Total** para agregar todos os anos.")

# --- Sidebar filtros ---
anos = sorted(df["Ano"].dropna().unique().tolist())
anos_display = ["Total"] + anos
selected_ano = st.sidebar.selectbox("Filtrar por Ano", anos_display, index=0)

# filtro aplicado
if selected_ano == "Total":
    df_f = df.copy()
else:
    df_f = df[df["Ano"] == selected_ano].copy()

# agregação por cliente
agg = df_f.groupby(["COD.CLI.", "CLIENTE"], as_index=False)["Valor"].sum()
agg = agg.sort_values("Valor", ascending=False)

# top 10
top_n = 10
top10 = agg.head(top_n).reset_index(drop=True)

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("Total Vendas (filtrado)", f"R$ {agg['Valor'].sum():,.2f}")
col2.metric("Clientes distintos (filtrado)", f"{agg['COD.CLI.'].nunique():,}")
col3.metric(f"Top {top_n} — Soma", f"R$ {top10['Valor'].sum():,.2f}")

st.markdown("---")

# Exibição principal: gráfico + tabela
left, right = st.columns([2,1])

with left:
    st.subheader(f"Top {top_n} Clientes por Valor — {'Todos os anos' if selected_ano=='Total' else 'Ano '+selected_ano}")
    if top10.shape[0] == 0:
        st.info("Nenhum dado para o filtro selecionado.")
    else:
        fig = px.bar(top10, x="CLIENTE", y="Valor", hover_data=["COD.CLI."], labels={"Valor":"Valor (R$)", "CLIENTE":"Cliente"})
        fig.update_layout(xaxis_tickangle=-45, margin=dict(t=30,b=150))
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Tabela — Top 10")
    st.dataframe(top10.style.format({"Valor":"R$ {:,.2f}"}), height=400)

st.markdown("---")
st.subheader("Dados filtrados (amostra)")
st.dataframe(df_f.head(200))

# Downloads
def to_excel_bytes(df_obj):
    towrite = BytesIO()
    df_obj.to_excel(towrite, index=False)
    towrite.seek(0)
    return towrite

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button("Baixar Top 10 (Excel)", data=to_excel_bytes(top10), file_name="top10_clientes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with col_dl2:
    st.download_button("Baixar Dados Filtrados (Excel)", data=to_excel_bytes(df_f), file_name="vendas_filtradas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("### Observações")
st.markdown("- Este app espera o arquivo `Banco de Dados Vendas.xlsx` na mesma pasta do app.")
st.markdown("- Colunas esperadas: `Ano`, `COD.CLI.`, `CLIENTE`, `Valor`.")
