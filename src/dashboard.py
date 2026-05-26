import os
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

try:
    from database import DB_PATH
except ModuleNotFoundError:
    from src.database import DB_PATH

CATSER_CODES = {
    # Grupo 1: Desenvolvimento de Novo Software
    "25852": ("Desenvolvimento de Novo Software - Java", "Desenvolvimento"),
    "25860": ("Desenvolvimento de Novo Software - PHP", "Desenvolvimento"),
    "25879": ("Desenvolvimento de Novo Software - .NET, ASP, Delphi, VB ou C++", "Desenvolvimento"),
    "25895": ("Desenvolvimento de Novo Software - Linguagens Web (Python, Ruby, Perl, etc.)", "Desenvolvimento"),
    "25887": ("Desenvolvimento de Novo Software - Mobile (Android, iOS)", "Desenvolvimento"),
    "25909": ("Desenvolvimento de Novo Software - Mainframe", "Desenvolvimento"),
    "25917": ("Desenvolvimento de Novo Software - Outras Linguagens", "Desenvolvimento"),
    
    # Grupo 2: Manutenção Evolutiva de Software
    "25925": ("Manutenção Evolutiva de Software - Java", "Manutenção Evolutiva"),
    "25933": ("Manutenção Evolutiva de Software - PHP", "Manutenção Evolutiva"),
    "25941": ("Manutenção Evolutiva de Software - .NET, ASP, Delphi, VB ou C++", "Manutenção Evolutiva"),
    "25968": ("Manutenção Evolutiva de Software - Linguagens Web (Python, Ruby, Perl, etc.)", "Manutenção Evolutiva"),
    "25950": ("Manutenção Evolutiva de Software - Mobile (Android, iOS)", "Manutenção Evolutiva"),
    "25976": ("Manutenção Evolutiva de Software - Mainframe", "Manutenção Evolutiva"),
    "25984": ("Manutenção Evolutiva de Software - Outras Linguagens", "Manutenção Evolutiva")
}

# ==========================================
# CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Governança de TI — Dashboard de Concentração",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para visual premium
st.markdown("""
    <style>
    .main-title {
        font-family: 'serif';
        font-size: 2.6rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-family: 'sans-serif';
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1F2937;
    }
    .metric-lbl {
        font-size: 0.9rem;
        color: #6B7280;
        text-transform: uppercase;
    }
    .cobit-card {
        background-color: #EFF6FF;
        border-left: 5px solid #2563EB;
        padding: 1.2rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO E CARGA DE DADOS
# ==========================================
if not os.path.exists(DB_PATH):
    st.error(f"Banco de dados não encontrado em {DB_PATH}. Por favor, rode `make db-real` ou `make db-mock` primeiro.")
    st.stop()

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Histórico pré-calculado de concentração
    df_hist = pd.read_sql_query("SELECT * FROM historico_concentracao", conn)
    
    # 2. Itens detalhados de contratos
    query_itens = """
        SELECT ic.*, c.ano_assinatura, c.valor_total AS valor_total_contrato, o.razao_social AS nome_orgao
        FROM item_contrato ic
        JOIN contrato c ON ic.contrato_id = c.id
        JOIN orgao o ON c.orgao_id = o.id
    """
    df_itens = pd.read_sql_query(query_itens, conn)
    df_itens["valor_total_item"] = df_itens["valor_unitario"] * df_itens["quantidade"]
    
    # 3. Contratos consolidados
    df_contratos = pd.read_sql_query(
        "SELECT c.id, c.numero_contrato, c.ano_assinatura, c.valor_total, o.razao_social AS nome_orgao "
        "FROM contrato c JOIN orgao o ON c.orgao_id = o.id WHERE c.valor_total > 0", conn
    )
    
    conn.close()
    return df_hist, df_itens, df_contratos

df_hist, df_itens, df_contratos = carregar_dados()

# ==========================================
# MENU LATERAL — FILTROS
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=70)
st.sidebar.header("Filtros do Painel")

# 1. Filtro de Ano
anos_disponiveis = sorted(int(x) for x in df_itens["ano_assinatura"].unique())
ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
ano_selecionado = st.sidebar.slider(
    "Ano de Assinatura",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1
)
anos_filtrados = list(range(ano_selecionado[0], ano_selecionado[1] + 1))

# 2. Filtro de Grupo de Serviço
grupos_disponiveis = list(df_itens["codigo_item"].map(lambda c: CATSER_CODES.get(c, ("", "Outros"))[1]).unique())
grupos_selecionados = st.sidebar.multiselect(
    "Grupo de Serviço",
    options=grupos_disponiveis,
    default=grupos_disponiveis
)

# 3. Filtro de Stacks Tecnológicas / CATSER
catser_detalhes = {k: f"{k} - {v[0].split(' - ')[-1]}" for k, v in CATSER_CODES.items()}
catser_options = sorted(CATSER_CODES.keys())
catser_selecionados = st.sidebar.multiselect(
    "Códigos CATSER (Tecnologias)",
    options=catser_options,
    default=catser_options,
    format_func=lambda x: catser_detalhes.get(x, x)
)

# 4. Configuração Avançada de Agregação
st.sidebar.markdown("---")
st.sidebar.subheader("Agregação Estatística")
metodo_hhi = st.sidebar.radio(
    "Agregação de HHI/CR4",
    options=["Ponderada por Faturamento", "Média Simples"],
    help="A média ponderada ajusta o peso de cada CATSER de acordo com o volume financeiro do contrato no ano, evitando que categorias minúsculas distorçam o resultado."
)

# ==========================================
# FILTRAGEM REATIVA DOS DADOS
# ==========================================
# Filtra tabela de itens
df_itens_f = df_itens[
    (df_itens["ano_assinatura"].isin(anos_filtrados)) &
    (df_itens["codigo_item"].isin(catser_selecionados))
]
# Injeta classificação do grupo de serviço para filtragem adicional
df_itens_f["tipo_grupo"] = df_itens_f["codigo_item"].map(lambda c: CATSER_CODES.get(c, ("", "Outros"))[1])
df_itens_f = df_itens_f[df_itens_f["tipo_grupo"].isin(grupos_selecionados)]

# Filtra contratos correspondentes aos itens filtrados
contratos_validos = df_itens_f["contrato_id"].unique()
df_contratos_f = df_contratos[df_contratos["id"].isin(contratos_validos)]

# ==========================================
# TÍTULO PRINCIPAL
# ==========================================
st.markdown("<h1 class='main-title'>Governança de TI & Compras Públicas</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Dashboard analítico concorrencial de Fábricas de Software na Administração Pública Federal (recorte pós-Lei 14.133/2021)</p>", unsafe_allow_html=True)

# ==========================================
# KPIs CARDS (Métricas Chave)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

total_faturamento = df_itens_f["valor_total_item"].sum()
total_contratos = df_contratos_f["id"].nunique()
total_fornecedores = df_itens_f["cnpj_fornecedor"].nunique()

# Cálculo dinâmico do HHI com base no filtro e método de agregação selecionado
hhi_valores = []
faturamento_valores = []
for (ano, cat), group in df_itens_f.groupby(["ano_assinatura", "codigo_item"]):
    fat_forn = group.groupby("cnpj_fornecedor")["valor_total_item"].sum()
    mkt_total = fat_forn.sum()
    if mkt_total > 0:
        shares = (fat_forn / mkt_total * 100).tolist()
        hhi = sum(s ** 2 for s in shares)
        hhi_valores.append(hhi)
        faturamento_valores.append(mkt_total)

if hhi_valores:
    if metodo_hhi == "Ponderada por Faturamento":
        avg_hhi = np.average(hhi_valores, weights=faturamento_valores)
    else:
        avg_hhi = np.mean(hhi_valores)
else:
    avg_hhi = 0.0

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Volume Licitado</div>
            <div class="metric-val">R$ {total_faturamento/1e6:.2f} M</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Total Contratos</div>
            <div class="metric-val">{total_contratos}</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Fornecedores Ativos</div>
            <div class="metric-val">{total_fornecedores}</div>
        </div>
    """, unsafe_allow_html=True)
with col4:
    lbl_hhi = "HHI Médio (Ponderado)" if metodo_hhi == "Ponderada por Faturamento" else "HHI Médio (Simples)"
    color_hhi = "#EF4444" if avg_hhi > 2500 else ("#F59E0B" if avg_hhi >= 1500 else "#10B981")
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color_hhi}">
            <div class="metric-lbl">{lbl_hhi}</div>
            <div class="metric-val">{avg_hhi:.1f}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================
# ABAS DE VISUALIZAÇÃO
# ==========================================
tab_graficos, tab_fornecedores, tab_estatistica, tab_cobit, tab_dados = st.tabs([
    "📈 Índices de Concentração",
    "🏢 Dominância de Fornecedores",
    "🧪 Modelagem Estatística",
    "📘 Governança COBIT",
    "📋 Dados dos Contratos"
])

# ------------------------------------------
# TAB 1: ÍNDICES DE CONCENTRAÇÃO
# ------------------------------------------
with tab_graficos:
    st.subheader("Evolução Temporal da Concorrência de Mercado")
    
    # Gerar DataFrame dinâmico dos índices de concentração com base nos filtros
    # Primeiro calculamos o HHI/CR4 de cada CATSER (mercado relevante) separadamente
    catser_indices = []
    for (ano, grupo, catser), group in df_itens_f.groupby(["ano_assinatura", "tipo_grupo", "codigo_item"]):
        fat_forn = group.groupby("cnpj_fornecedor")["valor_total_item"].sum()
        mkt_total = fat_forn.sum()
        if mkt_total > 0:
            shares = sorted((fat_forn / mkt_total * 100).tolist(), reverse=True)
            hhi = sum(s ** 2 for s in shares)
            cr4 = sum(shares[:4])
            catser_indices.append({
                "ano": ano,
                "tipo_grupo": grupo,
                "codigo_catser": catser,
                "hhi": hhi,
                "cr4": cr4,
                "faturamento": mkt_total
            })
            
    if catser_indices:
        df_catser_ind = pd.DataFrame(catser_indices)
        if metodo_hhi == "Ponderada por Faturamento":
            def weighted_avg(group, col):
                w = group["faturamento"]
                if w.sum() == 0:
                    return group[col].mean()
                return np.average(group[col], weights=w)
            
            df_dinamico = df_catser_ind.groupby(["ano", "tipo_grupo"]).apply(
                lambda g: pd.Series({
                    "hhi": weighted_avg(g, "hhi"),
                    "cr4": weighted_avg(g, "cr4")
                }),
                include_groups=False
            ).reset_index()
        else:
            df_dinamico = df_catser_ind.groupby(["ano", "tipo_grupo"]).agg({
                "hhi": "mean",
                "cr4": "mean"
            }).reset_index()
    else:
        df_dinamico = pd.DataFrame()
    
    if df_dinamico.empty:
        st.warning("Nenhum dado corresponde aos filtros selecionados para plotar a evolução temporal.")
    else:
        col_hhi, col_cr4 = st.columns(2)
        
        with col_hhi:
            fig_hhi = px.line(
                df_dinamico,
                x="ano",
                y="hhi",
                color="tipo_grupo",
                symbol="tipo_grupo",
                markers=True,
                labels={"ano": "Ano de Assinatura", "hhi": "HHI", "tipo_grupo": "Grupo de Serviço"},
                color_discrete_map={"Desenvolvimento": "#1f77b4", "Manutenção Evolutiva": "#ff7f0e", "Outros": "#7f7f7f"}
            )
            fig_hhi.update_traces(line=dict(width=3), marker=dict(size=8))
            
            # Reference lines for HHI thresholds
            fig_hhi.add_hline(y=1500, line_dash="dash", line_color="#808080", opacity=0.7)
            fig_hhi.add_hline(y=2500, line_dash="dash", line_color="#ff4b4b", opacity=0.7)
            
            # Annotations for thresholds
            fig_hhi.add_annotation(x=min(anos_filtrados), y=1100, text="Competitivo (< 1500)", showarrow=False, xanchor="left", font=dict(color="gray", size=10))
            fig_hhi.add_annotation(x=min(anos_filtrados), y=2000, text="Moderadamente Concentrado", showarrow=False, xanchor="left", font=dict(color="orange", size=10))
            fig_hhi.add_annotation(x=min(anos_filtrados), y=2900, text="Altamente Concentrado (> 2500)", showarrow=False, xanchor="left", font=dict(color="red", size=10))
            
            fig_hhi.update_layout(
                title=dict(text="<b>Evolução Temporal do Índice Herfindahl-Hirschman (HHI)</b>", font=dict(size=14)),
                xaxis=dict(tickmode="linear", tick0=2024, dtick=1),
                yaxis=dict(title="HHI (Escala DOJ/OCDE 0-10.000)", range=[0, 10000]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_hhi, use_container_width=True)
            
        with col_cr4:
            fig_cr4 = px.line(
                df_dinamico,
                x="ano",
                y="cr4",
                color="tipo_grupo",
                symbol="tipo_grupo",
                markers=True,
                labels={"ano": "Ano de Assinatura", "cr4": "CR4 (%)", "tipo_grupo": "Grupo de Serviço"},
                color_discrete_map={"Desenvolvimento": "#1f77b4", "Manutenção Evolutiva": "#ff7f0e", "Outros": "#7f7f7f"}
            )
            fig_cr4.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_cr4.update_layout(
                title=dict(text="<b>Evolução Temporal da Razão de Concentração (CR4)</b>", font=dict(size=14)),
                xaxis=dict(tickmode="linear", tick0=2024, dtick=1),
                yaxis=dict(title="CR4 (% de Mercado dos 4 Maiores Players)", range=[0, 100]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_cr4, use_container_width=True)
        
        st.markdown("""
        > **Interpretação Econômica**:
        > *   **HHI (Herfindahl-Hirschman Index)**: Penaliza mercados dominados por empresas gigantes. Quanto maior o índice, menor a concorrência. Níveis acima de **2.500** representam riscos críticos de monopólio ou oligopólio severo.
        > *   **CR4**: Revela o poder combinado das 4 maiores prestadoras de serviço. Se o CR4 atinge $80\%$, quatro empresas possuem virtualmente o controle de todo o recurso gasto sob aquele CATSER.
        """)

# ------------------------------------------
# TAB: DOMINÂNCIA DE FORNECEDORES
# ------------------------------------------
with tab_fornecedores:
    st.subheader("Dominância de Players no Mercado de TI Pública")
    st.markdown("""
        Esta seção detalha o faturamento total por fornecedor sob os filtros selecionados,
        evidenciando a participação das estatais de TI (SERPRO, PRODESP, etc.) e o nível de oligopólio.
    """)
    
    if df_itens_f.empty:
        st.warning("Nenhum dado para exibir com os filtros atuais.")
    else:
        # 1. Agrupar por fornecedor
        df_forn = df_itens_f.groupby(["cnpj_fornecedor", "razao_social_fornecedor"]).agg(
            faturamento=("valor_total_item", "sum"),
            n_contratos=("contrato_id", "nunique")
        ).reset_index().sort_values(by="faturamento", ascending=False)
        
        total_fat_filtro = df_forn["faturamento"].sum()
        if total_fat_filtro > 0:
            df_forn["share_%"] = (df_forn["faturamento"] / total_fat_filtro) * 100
        else:
            df_forn["share_%"] = 0.0
            
        # Classificação Estatais vs Privadas
        def classificar_tipo(row):
            name = row["razao_social_fornecedor"].upper()
            import re
            # Siglas curtas devem ser casadas como palavras inteiras para evitar falsos positivos
            # como "ATI" dentro de "INFORMATICA"
            estatais_regex = r"\b(SERPRO|DATAPREV|PRODESP|PRODEPA|PRODABEL|MGS|PRODERJ|ATI)\b"
            if re.search(estatais_regex, name):
                return "Estatal / Pública"
                
            # Expressões completas seguras para busca textual livre
            estatais_keywords = [
                "PROCESSAMENTO DE DADOS",
                "EMPRESA DE TECNOLOGIA",
                "TECNOLOGIA DA INFORMACAO E COMUNICACAO DO ESTADO",
                "IMPRENSA OFICIAL",
                "SERVICO FEDERAL"
            ]
            for kw in estatais_keywords:
                if kw in name:
                    return "Estatal / Pública"
            return "Privada"
            
        df_forn["tipo_fornecedor"] = df_forn.apply(classificar_tipo, axis=1)
        
        # Layout de 2 colunas: Top 10 e Donut
        col_forn1, col_forn2 = st.columns([2, 1])
        
        with col_forn1:
            st.markdown("**Top 10 Fornecedores por Faturamento**")
            df_top10 = df_forn.head(10).copy()
            # Inverter a ordem para o gráfico de barras horizontal (maior no topo)
            df_top10 = df_top10.iloc[::-1]
            
            fig_bar = px.bar(
                df_top10,
                x="faturamento",
                y="razao_social_fornecedor",
                text="share_%",
                orientation="h",
                labels={"faturamento": "Faturamento (R$)", "razao_social_fornecedor": "Fornecedor"},
                color="tipo_fornecedor",
                color_discrete_map={"Estatal / Pública": "#EF4444", "Privada": "#3B82F6"}
            )
            fig_bar.update_traces(
                texttemplate='%{text:.2f}%',
                textposition='outside',
                hovertemplate="<b>%{y}</b><br>Faturamento: R$ %{x:,.2f}<br>Participação: %{text:.2f}%<br>"
            )
            fig_bar.update_layout(
                xaxis=dict(title="Volume Contratado (R$)", gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(title=None),
                margin=dict(l=40, r=40, t=20, b=40),
                template="plotly_white",
                legend=dict(title="Tipo de Ente", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_forn2:
            st.markdown("**Participação por Tipo de Ente**")
            df_tipo = df_forn.groupby("tipo_fornecedor")["faturamento"].sum().reset_index()
            fig_pie = px.pie(
                df_tipo,
                values="faturamento",
                names="tipo_fornecedor",
                hole=0.4,
                color="tipo_fornecedor",
                color_discrete_map={"Estatal / Pública": "#EF4444", "Privada": "#3B82F6"}
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Faturamento Total: R$ %{value:,.2f}<br>"
            )
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                template="plotly_white"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Tabela resumo abaixo dos gráficos
        st.markdown("**Resumo dos Fornecedores**")
        df_tabela = df_forn.copy()
        df_tabela["faturamento_m"] = df_tabela["faturamento"] / 1e6
        df_tabela = df_tabela.rename(columns={
            "razao_social_fornecedor": "Fornecedor",
            "faturamento_m": "Faturamento (M R$)",
            "n_contratos": "Contratos",
            "share_%": "Participação (%)",
            "tipo_fornecedor": "Tipo"
        })
        st.dataframe(
            df_tabela[["Fornecedor", "Tipo", "Faturamento (M R$)", "Contratos", "Participação (%)"]],
            use_container_width=True,
            column_config={
                "Faturamento (M R$)": st.column_config.NumberColumn(format="R$ %.2f M"),
                "Participação (%)": st.column_config.NumberColumn(format="%.2f %%")
            },
            hide_index=True
        )

# ------------------------------------------
# TAB 3: MODELAGEM E TESTES ESTATÍSTICOS
# ------------------------------------------
with tab_estatistica:
    st.subheader("Validação de Hipóteses Científicas")
    
    col_stat1, col_stat2 = st.columns(2)
    
    # Processamento para o Spearman Dinâmico
    lista_correlacao = []
    for (ano, cat), group in df_itens_f.groupby(["ano_assinatura", "codigo_item"]):
        fat_forn = group.groupby("cnpj_fornecedor")["valor_total_item"].sum()
        mkt_total = fat_forn.sum()
        if mkt_total > 0:
            shares = (fat_forn / mkt_total * 100).tolist()
            hhi = sum(s ** 2 for s in shares)
            lista_correlacao.append({
                "codigo": cat,
                "faturamento_m": mkt_total / 1e6,
                "hhi": hhi
            })
    df_corr = pd.DataFrame(lista_correlacao)
    
    with col_stat1:
        st.markdown("**1. Correlação de Spearman (Faturamento vs. HHI)**")
        if len(df_corr) < 3:
            st.info("São necessários dados de pelo menos 3 combinações de CATSER/Ano filtradas para rodar a correlação.")
        else:
            spearman_rho, spearman_p = stats.spearmanr(df_corr["faturamento_m"], df_corr["hhi"])
            slope, intercept, r_value, p_value, std_err = stats.linregress(df_corr["faturamento_m"], df_corr["hhi"])
            
            # Calculamos a reta de tendência
            x_vals = np.linspace(df_corr["faturamento_m"].min(), df_corr["faturamento_m"].max(), 100)
            y_vals = slope * x_vals + intercept
            
            fig_sp = px.scatter(
                df_corr,
                x="faturamento_m",
                y="hhi",
                text="codigo",
                labels={"faturamento_m": "Faturamento Anual (Milhões R$)", "hhi": "Índice HHI", "codigo": "CATSER"},
                color_discrete_sequence=["#2ca02c"]
            )
            fig_sp.update_traces(
                textposition='top center',
                marker=dict(size=10, opacity=0.8, line=dict(width=1, color="black"))
            )
            fig_sp.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name="Reta de Tendência",
                line=dict(color="#d62728", width=2, dash="dash"),
                showlegend=False
            ))
            
            fig_sp.update_layout(
                title=dict(text="<b>Faturamento de Mercado vs. Concentração</b>", font=dict(size=12)),
                xaxis=dict(title="Faturamento Anual (Milhões R$)", gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(title="HHI", gridcolor="rgba(0,0,0,0.05)"),
                margin=dict(l=40, r=40, t=50, b=40),
                template="plotly_white",
                showlegend=False
            )
            st.plotly_chart(fig_sp, use_container_width=True)
            
            st.metric("Coeficiente de Spearman (ρ)", f"{spearman_rho:.3f}")
            sig_text = "Rejeita-se H0 (Significativo)" if spearman_p < 0.05 else "Falha em rejeitar H0 (Não significativo)"
            st.write(f"**p-valor**: `{spearman_p:.5f}` | **Significância (α=0.05)**: {sig_text}")
            st.caption("Investiga se mercados com maior investimento (faturamento) tendem a atrair concorrência (reduzindo o HHI) ou concentrar ainda mais.")
            
    with col_stat2:
        st.markdown("**2. Teste Kruskal-Wallis (Distribuição de Contratos)**")
        if df_contratos_f.empty or len(anos_filtrados) < 2:
            st.info("Selecione pelo menos 2 anos no menu lateral para comparar distribuições orçamentárias.")
        else:
            grupos_kw = [df_contratos_f[df_contratos_f["ano_assinatura"] == a]["valor_total"].dropna().tolist() for a in anos_filtrados]
            # Remove listas vazias
            grupos_kw = [g for g in grupos_kw if g]
            
            if len(grupos_kw) < 2:
                st.info("Dados insuficientes para rodar o teste Kruskal-Wallis.")
            else:
                kw_stat, kw_p = stats.kruskal(*grupos_kw)
                
                df_boxplot = df_contratos_f.copy()
                fig_kw = px.box(
                    df_boxplot,
                    x="ano_assinatura",
                    y="valor_total",
                    points="all",
                    labels={"ano_assinatura": "Ano de Assinatura", "valor_total": "Valor Contratual (R$)"},
                    color_discrete_sequence=["#1f77b4"]
                )
                
                fig_kw.update_layout(
                    title=dict(text="<b>Distribuição do Valor dos Contratos (Escala Logarítmica)</b>", font=dict(size=12)),
                    xaxis=dict(type="category", title="Ano de Assinatura", gridcolor="rgba(0,0,0,0.05)"),
                    yaxis=dict(
                        type="log",
                        title="Valor Contratual (R$)",
                        gridcolor="rgba(0,0,0,0.05)",
                        tickvals=[1000, 10000, 100000, 1000000, 10000000],
                        ticktext=["R$ 1k", "R$ 10k", "R$ 100k", "R$ 1M", "R$ 10M"]
                    ),
                    margin=dict(l=40, r=40, t=50, b=40),
                    template="plotly_white"
                )
                st.plotly_chart(fig_kw, use_container_width=True)
                
                st.metric("Estatística H", f"{kw_stat:.3f}")
                kw_sig_text = "Rejeita-se H0 (Mudança estrutural)" if kw_p < 0.05 else "Falha em rejeitar H0 (Sem variação significativa)"
                st.write(f"**p-valor**: `{kw_p:.4f}` | **Significância (α=0.05)**: {kw_sig_text}")
                st.caption("Verifica se os valores contratuais praticados mantiveram um padrão homogêneo ou se sofreram distorções/inflação severa nos anos comparados.")

# ------------------------------------------
# TAB 3: GOVERNANÇA COBIT (APO10 & APO12)
# ------------------------------------------
with tab_cobit:
    st.subheader("Mapeamento Prático de Governança corporativa (COBIT 2019)")
    
    st.markdown("""
    Os resultados quantitativos de concentração calculados neste painel servem como insumo para a governança de tecnologia do Governo Federal, principalmente nas seguintes áreas:
    """)
    
    st.markdown("""
    <div class="cobit-card">
        <h4>APO10 — Gerenciar Fornecedores (COBIT 2019)</h4>
        <p>O foco do processo APO10 é maximizar o valor gerado pelos fornecedores de TI mitigando riscos de relacionamento e dependência contratual.</p>
        <ul>
            <li><b>APO10.02 (Selecionar Fornecedores):</b> O painel mostra se o ambiente licitatório está competitivo. Em mercados com <b>HHI > 2500</b>, a governança deve flexibilizar editais para estimular a entrada de novos concorrentes e diminuir custos.</li>
            <li><b>APO10.05 (Monitorar Risco do Fornecedor):</b> O HHI atua como um <b>KRI (Key Risk Indicator)</b>. O aumento do HHI em stacks de software essenciais sinaliza alta probabilidade de <i>vendor lock-in</i> (fidelização forçada) e dependência de poucos fornecedores.</li>
        </ul>
    </div>
    
    <div class="cobit-card">
        <h4>APO12 — Gerenciar Riscos (COBIT 2019)</h4>
        <p>O foco do processo APO12 é identificar, avaliar e mitigar riscos operacionais relacionados a TI.</p>
        <ul>
            <li><b>APO12.01 (Identificar Cenários de Risco):</b> Nichos altamente concentrados (como o de Mainframe) onde o HHI beira os 10.000 são classificados como risco crítico. Um incidente com o fornecedor dominante pode paralisar serviços governamentais chaves.</li>
            <li><b>APO12.02 (Análise de Impacto):</b> Permite à governança traçar planos de contingência, exigindo das contratações arquiteturas mais modulares ou a adoção de tecnologias alternativas de mercado aberto.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar alertas dinâmicos com base nos dados reais exibidos
    if avg_hhi > 2500:
        st.error(f"⚠️ **Alerta de Governança APO10/APO12**: O HHI médio atual de **{avg_hhi:.1f}** indica um mercado de Fábrica de Software **Altamente Concentrado**. Risco crítico de oligopolização e *vendor lock-in*. Ações de atração de novos fornecedores e planos de transição de tecnologia são recomendados.")
    elif avg_hhi >= 1500:
        st.warning(f"⚠️ **Alerta de Governança APO10**: O HHI médio atual de **{avg_hhi:.1f}** indica um mercado **Moderadamente Concentrado**. Recomenda-se acompanhar de perto a concorrência nas próximas contratações.")
    else:
        st.success(f"✅ **Governança OK**: O HHI médio atual de **{avg_hhi:.1f}** indica um mercado **Competitivo** e saudável. Excelente cenário concorrencial para novos pregões eletrônicos.")

# ------------------------------------------
# TAB 4: DADOS DOS CONTRATOS
# ------------------------------------------
with tab_dados:
    st.subheader("Base de Contratos e Itens Filtrados")
    st.write("Abaixo estão listados os itens de contrato que atendem aos filtros ativos no painel lateral:")
    
    exibir_colunas = [
        "ano_assinatura", "codigo_item", "descricao", "cnpj_fornecedor", 
        "razao_social_fornecedor", "quantidade", "valor_unitario", "valor_total_item",
        "nome_orgao", "esfera", "estado"
    ]
    df_exibicao = df_itens_f[exibir_colunas].copy()
    df_exibicao.rename(columns={
        "ano_assinatura": "Ano",
        "codigo_item": "CATSER",
        "descricao": "Descrição",
        "cnpj_fornecedor": "CNPJ Fornecedor",
        "razao_social_fornecedor": "Razão Social Fornecedor",
        "quantidade": "Qtd",
        "valor_unitario": "Valor Unit.",
        "valor_total_item": "Valor Total",
        "nome_orgao": "Órgão Licitante",
        "esfera": "Esfera",
        "estado": "UF"
    }, inplace=True)
    
    st.dataframe(df_exibicao, use_container_width=True)
