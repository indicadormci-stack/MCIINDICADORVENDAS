
import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Banco de Dados Vendas.xlsx")

df = load_data()
df["Ano"] = df["Ano"].astype(str)

# Menu lateral
st.sidebar.title("📊 Indicadores")
pagina = st.sidebar.radio("Navegação", ["Análise de Vendas", "Clientes Perdidos"])

# ================= Análise de Vendas =================
if pagina == "Análise de Vendas":
    st.title("📈 Análise de Vendas — Top Clientes")

    anos = sorted(df["Ano"].unique().tolist())
    selected_ano = st.sidebar.selectbox("Selecione o Ano", ["Total"] + anos)
    top_n = st.sidebar.selectbox("Top N clientes", ["Top 5", "Top 10", "Top 50", "Todos"])

    # Filtro de ano
    if selected_ano != "Total":
        df_filtro = df[df["Ano"] == selected_ano]
    else:
        df_filtro = df.copy()

    df_group = df_filtro.groupby(["COD.CLI.", "CLIENTE"], as_index=False)["Valor"].sum()

    # Aplicar filtro de top
    if top_n != "Todos":
        n_val = int(top_n.split()[1])
        df_group = df_group.sort_values("Valor", ascending=False).head(n_val)
    else:
        n_val = len(df_group)
        df_group = df_group.sort_values("Valor", ascending=False)

    df_group.insert(0, "Posição", range(1, len(df_group) + 1))

    st.subheader(f"Top {n_val} Clientes por Valor — {'Todos os anos' if selected_ano=='Total' else 'Ano ' + selected_ano}")
    fig = px.bar(df_group, x="Valor", y="CLIENTE", orientation="h", text="Valor")
    fig.update_traces(texttemplate="R$ %{x:,.2f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📋 Tabela — Top Clientes")
    st.dataframe(df_group, height=500, use_container_width=True)

    # Busca por cliente
    st.markdown("### 🔎 Pesquisa por Cliente")
    termo = st.text_input("Digite nome ou código do cliente")
    if termo:
        termo_lower = termo.lower()
        df_busca = df[df["CLIENTE"].str.lower().str.contains(termo_lower) | df["COD.CLI."].astype(str).str.contains(termo)]
        st.dataframe(df_busca.groupby(["Ano", "CLIENTE"], as_index=False)["Valor"].sum())

# ================= Clientes Perdidos =================
elif pagina == "Clientes Perdidos":
    st.title("📉 Clientes que não compraram mais")

    # Seleção de anos base (múltiplos)
    anos = sorted(df["Ano"].unique().tolist())
    anos_base = st.sidebar.multiselect("Selecione ano(s) base", anos, default=anos[-2:])

    clientes_base = df[df["Ano"].isin(anos_base)]["COD.CLI."].unique()
    clientes_posteriores = df[df["Ano"].astype(int) > max(map(int, anos_base))]["COD.CLI."].unique()
    clientes_perdidos = set(clientes_base) - set(clientes_posteriores)

    df_perdidos = df[df["COD.CLI."].isin(clientes_perdidos) & df["Ano"].isin(anos_base)]
    df_perdidos = df_perdidos.groupby(["COD.CLI.", "CLIENTE"], as_index=False)["Valor"].sum()
    df_perdidos = df_perdidos.sort_values("Valor", ascending=False)

    col1, col2 = st.columns(2)
    col1.metric("🚨 Clientes perdidos", len(df_perdidos))
    col2.metric("💸 Valor perdido", f"R$ {df_perdidos['Valor'].sum():,.2f}")
    st.dataframe(df_perdidos, use_container_width=True)

    # --- Novo gráfico consolidado ---
    st.markdown("### 📊 Top Clientes Perdidos por Valor")
    top_filter = st.selectbox("Selecionar Top N", ["Top 5", "Top 10", "Top 20", "Todos"], index=1)

    if top_filter != "Todos":
        n_val = int(top_filter.split()[1])
        df_plot = df_perdidos.head(n_val)
    else:
        n_val = len(df_perdidos)
        df_plot = df_perdidos

    fig_top = px.bar(df_plot.sort_values("Valor", ascending=True),
                     x="Valor", y="CLIENTE", orientation="h", text="Valor",
                     labels={"Valor": "Valor (R$)", "CLIENTE": "Cliente"})
    fig_top.update_traces(texttemplate="R$ %{x:,.2f}", textposition="outside")
    st.plotly_chart(fig_top, use_container_width=True)

    # --- Filtro por cliente individual ---
    clientes_lista = df_perdidos["CLIENTE"].tolist()
    cliente_escolhido = st.selectbox("🔎 Selecionar cliente para análise", ["(Nenhum)"] + clientes_lista)

    if cliente_escolhido != "(Nenhum)":
        df_cliente = df[df["CLIENTE"] == cliente_escolhido].groupby("Ano", as_index=False)["Valor"].sum()
        todos_anos = pd.DataFrame({"Ano": anos})
        df_cliente = todos_anos.merge(df_cliente, on="Ano", how="left").fillna(0)

        st.markdown(f"### 📊 Evolução do cliente: {cliente_escolhido}")
        fig = px.bar(df_cliente, x="Ano", y="Valor", text="Valor",
                     labels={"Valor": "Valor (R$)", "Ano": "Ano"})
        fig.update_traces(texttemplate="R$ %{y:,.2f}")
        st.plotly_chart(fig, use_container_width=True)
