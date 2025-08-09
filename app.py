import streamlit as st
import pandas as pd
import plotly.express as px
from babel.numbers import format_currency
from forex_python.converter import CurrencyRates

# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================
st.set_page_config(
    page_title="Dashboard de Salários na Área de Dados",
    page_icon="📊",
    layout="wide",
)

# ==========================
# FUNÇÃO PARA CARREGAR DADOS
# ==========================
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/vqrca/dashboard_salarios_dados/refs/heads/main/dados-imersao-final.csv"
    return pd.read_csv(url)

# ==========================
# FUNÇÃO PARA PEGAR TAXAS EM TEMPO REAL (CACHE 1 HORA)
# ==========================
@st.cache_data(ttl=3600)
def pegar_taxas():
    try:
        c = CurrencyRates()
        return {
            "USD": 1.0,
            "BRL": c.get_rate('USD', 'BRL'),
            "EUR": c.get_rate('USD', 'EUR'),
        }
    except:
        # Taxas de fallback se a API falhar
        return {"USD": 1.0, "BRL": 5.5, "EUR": 0.85}

# ==========================
# INÍCIO DA APP
# ==========================
df = carregar_dados()
df = df.dropna(subset=['usd'])

taxas = pegar_taxas()

# ==========================
# FILTROS BARRA LATERAL
# ==========================
st.sidebar.header("🔍 Filtros")

anos_selecionados = st.sidebar.multiselect(
    "Ano",
    sorted(df['ano'].unique()),
    default=sorted(df['ano'].unique())
)

senioridades_selecionadas = st.sidebar.multiselect(
    "Senioridade",
    sorted(df['senioridade'].unique()),
    default=sorted(df['senioridade'].unique())
)

contratos_selecionados = st.sidebar.multiselect(
    "Tipo de Contrato",
    sorted(df['contrato'].unique()),
    default=sorted(df['contrato'].unique())
)

tamanhos_selecionados = st.sidebar.multiselect(
    "Tamanho da Empresa",
    sorted(df['tamanho_empresa'].unique()),
    default=sorted(df['tamanho_empresa'].unique())
)

moeda_selecionada = st.sidebar.selectbox(
    "💱 Moeda",
    options=["USD", "BRL", "EUR"],
    index=0
)

# ==========================
# FILTRAGEM DOS DADOS
# ==========================
df_filtrado = df[
    (df['ano'].isin(anos_selecionados)) &
    (df['senioridade'].isin(senioridades_selecionadas)) &
    (df['contrato'].isin(contratos_selecionados)) &
    (df['tamanho_empresa'].isin(tamanhos_selecionados))
]

# CONVERTE SALÁRIOS USANDO TAXAS EM TEMPO REAL
df_filtrado['valor_convertido'] = df_filtrado['usd'] * taxas[moeda_selecionada]

# ==========================
# CONTEÚDO PRINCIPAL
# ==========================
st.title("🎲 Dashboard de Análise de Salários na Área de Dados")
st.markdown("Explore os dados salariais nos últimos anos. Use os filtros à esquerda para refinar sua análise.")

st.subheader(f"📌 Métricas gerais (Salário anual em {moeda_selecionada})")

if not df_filtrado.empty:
    salario_medio = df_filtrado['valor_convertido'].mean()
    salario_maximo = df_filtrado['valor_convertido'].max()
    total_registros = df_filtrado.shape[0]
    cargo_mais_frequente = df_filtrado["cargo"].mode()[0]
else:
    salario_medio, salario_maximo, total_registros, cargo_mais_frequente = 0, 0, 0, "-"

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Salário médio", format_currency(salario_medio, moeda_selecionada, locale="en_US"))
col2.metric("🏆 Salário máximo", format_currency(salario_maximo, moeda_selecionada, locale="en_US"))
col3.metric("📊 Total de registros", f"{total_registros:,}")
col4.metric("👔 Cargo mais frequente", cargo_mais_frequente)

st.markdown("---")

px.defaults.template = "plotly_white"

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado.groupby('cargo')['valor_convertido']
            .mean()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )
        fig_cargos = px.bar(
            top_cargos,
            x='valor_convertido',
            y='cargo',
            orientation='h',
            title=f"Top 10 cargos por salário médio ({moeda_selecionada})",
            labels={'valor_convertido': f"Média salarial anual ({moeda_selecionada})", 'cargo': ''},
            color='valor_convertido',
            color_continuous_scale='Viridis'
        )
        fig_cargos.update_layout(title_x=0.1, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_cargos, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")

with col_graf2:
    if not df_filtrado.empty:
        nbins = max(10, min(50, len(df_filtrado) // 5))
        fig_hist = px.histogram(
            df_filtrado,
            x='valor_convertido',
            nbins=nbins,
            title=f"Distribuição de salários anuais ({moeda_selecionada})",
            labels={'valor_convertido': f"Faixa salarial ({moeda_selecionada})", 'count': ''},
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.update_layout(title_x=0.1, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no histograma.")

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    if not df_filtrado.empty:
        remoto_contagem = df_filtrado['remoto'].value_counts().reset_index()
        remoto_contagem.columns = ['Tipo de Trabalho', 'Quantidade']
        fig_remoto = px.pie(
            remoto_contagem,
            names='Tipo de Trabalho',
            values='Quantidade',
            title='Proporção dos tipos de trabalho',
            hole=0.5,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_remoto.update_traces(textinfo='percent+label')
        fig_remoto.update_layout(title_x=0.1, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_remoto, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de trabalho remoto.")

with col_graf4:
    if not df_filtrado.empty:
        df_ds = df_filtrado[df_filtrado['cargo'] == 'Data Scientist']
        if not df_ds.empty:
            media_ds_pais = df_ds.groupby('residencia_iso3')['valor_convertido'].mean().reset_index()
            fig_mapa = px.choropleth(
                media_ds_pais,
                locations='residencia_iso3',
                color='valor_convertido',
                color_continuous_scale='RdYlGn',
                title=f"Salário médio de Cientista de Dados por país ({moeda_selecionada})",
                labels={'valor_convertido': f"Salário médio ({moeda_selecionada})", 'residencia_iso3': 'País'}
            )
            fig_mapa.update_layout(title_x=0.1, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.warning("Nenhum dado de Data Scientist para exibir no mapa.")
    else:
        st.warning("Nenhum dado para exibir no gráfico de países.")

st.markdown("---")

if not df_filtrado.empty:
    st.subheader(f"📈 Evolução do salário médio por ano ({moeda_selecionada})")
    evolucao = df_filtrado.groupby('ano')['valor_convertido'].mean().reset_index()
    fig_line = px.line(
        evolucao,
        x='ano',
        y='valor_convertido',
        markers=True,
        labels={'ano': 'Ano', 'valor_convertido': f"Salário médio ({moeda_selecionada})"},
        color_discrete_sequence=['#2ca02c']
    )
    fig_line.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

st.subheader("📋 Dados Detalhados")
st.dataframe(df_filtrado)

csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="💾 Baixar CSV filtrado",
    data=csv,
    file_name="salarios_filtrados.csv",
    mime="text/csv"
)
