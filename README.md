# Streamlit — Vendas por Cliente

App simples em Streamlit que lê o arquivo `Banco de Dados Vendas.xlsx` (planilha `Banco de Dados`) e mostra:
- Filtro por ano (ou **Total** para todos os anos)
- Indicador Top 10 clientes por valor
- Gráfico e tabela do Top 10
- Download do Top 10 e dos dados filtrados

Como rodar:
1. Criar um ambiente virtual (recomendado) e instalar dependências:
```
pip install -r requirements.txt
```
2. Rodar o app:
```
streamlit run app.py
```

Observação: o arquivo Excel já está incluído nesta pasta. Se você subir para o GitHub, mantenha o Excel no repositório ou ajuste o caminho de leitura para apontar a um bucket/fonte externa.