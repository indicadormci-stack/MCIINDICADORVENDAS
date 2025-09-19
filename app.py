import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import unicodedata

# --- Config ---
st.set_page_config(page_title="Vendas por Cliente", layout="wide")

# --- Sidebar controle de páginas ---
pagina = st.sidebar.radio("📊 Escolha a visualização:", ["Análise de Vendas", "Clientes Perdidos"])

# --- Carrega dados ---
@st.cache_data
def load_data(path="Banco de Dados Vendas.xlsx"):
    df = pd.read_excel(path, sheet_name="Banco de Dados")
    df = df.rename(columns=lambda x: x.strip())
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Ano"] = df["Ano"].astype(str)
    return df

df = load_data()

if pagina == "Análise de Vendas":
    st.title("📈 Análise de Vendas — Top Clientes")
    st.markdown("Interface dinâmica para visualizar vendas por cliente e por ano. Use os filtros laterais para selecionar um ano e a quantidade de clientes no ranking.")

    # --- Filtro por cliente ou código (ignora acentos) ---
    def normalize_txt(txt):
        if isinstance(txt, str):
            return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8").lower()
        return str(txt).lower()

    search_query = st.text_input("🔎 Pesquisar Cliente (por nome ou código):").strip()
    if search_query:
        search_norm = normalize_txt(search_query)
        df = df[df["CLIENTE"].apply(lambda x: search_norm in normalize_txt(x)) |
                df["COD.CLI."].astype(str).apply(lambda x: search_norm in x.lower())]

    # --- Sidebar filtros ---
    anos = sorted(df["Ano"].dropna().unique().tolist())
    anos_display = ["Total"] + anos
    selected_ano = st.sidebar.selectbox("Filtrar por Ano", anos_display, index=0)

    top_options = {"Top 5": 5, "Top 10": 10, "Top 50": 50, "Todos": None}
    selected_top = st.sidebar.selectbox("Quantidade de clientes", list(top_options.keys()))

    # filtro aplicado
    if selected_ano == "Total":
        df_f = df.copy()
    else:
        df_f = df[df["Ano"] == selected_ano].copy()

    # agregação por cliente
    agg = df_f.groupby(["COD.CLI.", "CLIENTE"], as_index=False)["Valor"].sum()
    agg = agg.sort_values("Valor", ascending=False)

    # aplica o filtro top N
    top_n = top_options[selected_top]
    if top_n is not None:
        top_df = agg.head(top_n).reset_index(drop=True)
    else:
        top_df = agg.reset_index(drop=True)

    # Métricas principais
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Vendas (filtrado)", f"R$ {agg['Valor'].sum():,.2f}")
    col2.metric("👥 Clientes distintos", f"{agg['COD.CLI.'].nunique():,}")
    col3.metric(f"🏆 {selected_top}", f"R$ {top_df['Valor'].sum():,.2f}")

    st.markdown("---")

    # --- Exibição principal: gráfico + tabela ---
    if selected_top != "Todos":
        titulo_top = f"{selected_top} (até {len(top_df)} clientes exibidos)"
    else:
        titulo_top = "Todos os clientes"

    st.markdown(f"## 📊 {titulo_top} por Valor — {'Todos os anos' if selected_ano == 'Total' else 'Ano ' + selected_ano}")

    if top_df.shape[0] == 0:
        st.info("Nenhum dado para o filtro selecionado.")
    else:
        # Destaque no Top 1
        if len(top_df) > 0:
            top_df["Cor"] = ["#ff7f0e"] + ["#1f77b4"] * (len(top_df)-1)
        else:
            top_df["Cor"] = []

        fig = px.bar(
            top_df,
            x="Valor",
            y="CLIENTE",
            orientation="h",
            text="Valor",
            hover_data=["COD.CLI."],
            color="Cor",
            color_discrete_map="identity",
            labels={"Valor": "Valor (R$)", "CLIENTE": "Cliente"}
        )
        fig.update_traces(texttemplate="R$ %{x:,.2f}", textposition="outside")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=30, b=30, l=100, r=40), showlegend=False, height=600)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"## 📑 Tabela — {titulo_top}")
    df_table = top_df.drop(columns=["Cor"]).copy() if "Cor" in top_df.columns else top_df.copy()
    df_table["Valor"] = df_table["Valor"].map("R$ {:,.2f}".format)
    df_table.index = df_table.index + 1
    st.dataframe(df_table)

    if selected_top != "Todos" and len(top_df) < (top_n if top_n is not None else len(top_df)):
        st.caption(f"⚠️ Apenas {len(top_df)} clientes encontrados para o filtro aplicado.")

    st.markdown("---")
    st.subheader("📋 Dados filtrados (amostra)")
    df_preview = df_f.head(200).copy()
    df_preview["Valor"] = df_preview["Valor"].map("R$ {:,.2f}".format)
    df_preview.index = df_preview.index + 1
    st.dataframe(df_preview)

    # --- Downloads ---
    def to_excel_bytes(df_obj):
        towrite = BytesIO()
        df_obj.to_excel(towrite, index=False)
        towrite.seek(0)
        return towrite

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Baixar Ranking (Excel)",
            data=to_excel_bytes(top_df.drop(columns=["Cor"]) if "Cor" in top_df.columns else top_df),
            file_name="ranking_clientes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_dl2:
        st.download_button(
            "⬇️ Baixar Dados Filtrados (Excel)",
            data=to_excel_bytes(df_f),
            file_name="vendas_filtradas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif pagina == "Clientes Perdidos":
    st.title("📉 Clientes que não compraram mais")
    anos = sorted(df["Ano"].dropna().unique().tolist())
    ano_base = st.sidebar.selectbox("Selecione o ano base", anos)

    # Clientes do ano base
    clientes_ano = df[df["Ano"] == ano_base]["COD.CLI."].unique()
    # Clientes de anos posteriores
    clientes_posteriores = df[df["Ano"] > ano_base]["COD.CLI."].unique()
    # Diferença: clientes que sumiram
    clientes_perdidos = set(clientes_ano) - set(clientes_posteriores)

    df_perdidos = df[(df["Ano"] == ano_base) & (df["COD.CLI."].isin(clientes_perdidos))]
    df_perdidos = df_perdidos.groupby(["COD.CLI.", "CLIENTE"], as_index=False)["Valor"].sum()
    df_perdidos = df_perdidos.sort_values("Valor", ascending=False)

    col1, col2 = st.columns(2)
    col1.metric("🚨 Clientes perdidos", len(df_perdidos))
    col2.metric("💸 Valor perdido", f"R$ {df_perdidos['Valor'].sum():,.2f}")
    df_perdidos.index = df_perdidos.index + 1
    st.dataframe(df_perdidos)

    # --- Download Clientes Perdidos ---
    def to_excel_bytes(df_obj):
        towrite = BytesIO()
        df_obj.to_excel(towrite, index=False)
        towrite.seek(0)
        return towrite

    st.download_button(
        "⬇️ Baixar Clientes Perdidos (Excel)",
        data=to_excel_bytes(df_perdidos),
        file_name=f"clientes_perdidos_{ano_base}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
