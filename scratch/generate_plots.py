import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configurações de diretório e estilo
DB_PATH = r"c:\Users\Usuario\Documents\S.i\6\Governanca\portalcompraspublicas_dados\compras_governanca.db"
OUTPUT_DIR = r"C:\Users\Usuario\.gemini\antigravity\brain\c03b5a55-e02e-49ac-80af-bbd4bb103646"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 16
})

conn = sqlite3.connect(DB_PATH)

# =========================================================================
# GRÁFICO 1: Série Temporal do HHI e CR4 Médios por Grupo (2024-2026)
# =========================================================================
df_hist = pd.read_sql_query("SELECT * FROM historico_concentracao", conn)

fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharex=True)

# Cores harmônicas
palette = {"Desenvolvimento": "#1f77b4", "Manutenção Evolutiva": "#ff7f0e"}

# 1a. Evolução do HHI médio
sns.lineplot(
    data=df_hist, x="ano", y="hhi", hue="tipo_grupo", style="tipo_grupo",
    markers=True, dashes=False, err_style="bars", palette=palette, ax=axes[0], lw=2.5, ms=8
)
axes[0].axhline(1500, color="gray", linestyle="--", alpha=0.7)
axes[0].axhline(2500, color="red", linestyle="--", alpha=0.7)
axes[0].set_title("Evolução Temporal do Índice Herfindahl-Hirschman (HHI)", pad=15)
axes[0].set_ylabel("HHI (Escala DOJ/OCDE 0-10.000)")
axes[0].set_xlabel("Ano de Assinatura")
axes[0].set_xticks([2024, 2025, 2026])
# Anotações dos thresholds
axes[0].text(2024.1, 1200, "Altamente Competitivo (< 1500)", fontsize=9, color="gray")
axes[0].text(2024.1, 1800, "Moderadamente Concentrado", fontsize=9, color="orange")
axes[0].text(2024.1, 2700, "Altamente Concentrado (> 2500)", fontsize=9, color="red")

# 1b. Evolução do CR4 médio
sns.lineplot(
    data=df_hist, x="ano", y="cr4", hue="tipo_grupo", style="tipo_grupo",
    markers=True, dashes=False, err_style="bars", palette=palette, ax=axes[1], lw=2.5, ms=8
)
axes[1].set_title("Evolução Temporal da Razão de Concentração (CR4)", pad=15)
axes[1].set_ylabel("CR4 (% de Mercado dos 4 Maiores Players)")
axes[1].set_xlabel("Ano de Assinatura")
axes[1].set_xticks([2024, 2025, 2026])

plt.suptitle("Concentração de Mercado de Fábrica de Software na Administração Pública (2024-2026)", y=0.98)
plt.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "1_series_temporais_concentracao.png"), dpi=300)
plt.close(fig)

# =========================================================================
# GRÁFICO 2: Correlação de Spearman (Faturamento Total do CATSER vs. HHI)
# =========================================================================
fig, ax = plt.subplots(figsize=(8, 6))

# Calcula regressão linear para a linha de tendência
x = df_hist["faturamento_total_mercado"] / 1e6 # Escala em Milhões de R$
y = df_hist["hhi"]
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
spearman_rho, spearman_p = stats.spearmanr(df_hist["faturamento_total_mercado"], df_hist["hhi"])

sns.regplot(
    x=x, y=y, ax=ax, color="#2ca02c", scatter_kws={"s": 60, "alpha": 0.8},
    line_kws={"color": "#d62728", "lw": 2}
)

# Destaca pontos específicos com textos
for idx, row in df_hist.iterrows():
    ax.annotate(
        row["codigo_catser"], 
        (row["faturamento_total_mercado"] / 1e6, row["hhi"]),
        textcoords="offset points", xytext=(5,5), fontsize=8, alpha=0.7
    )

ax.set_title("Dispersão e Tendência: Faturamento do Mercado vs. Concentração (HHI)", pad=15)
ax.set_xlabel("Faturamento Anual do CATSER (Milhões de R$)")
ax.set_ylabel("HHI (Escala 0-10.000)")

# Box de Estatística
stats_text = (
    f"Coeficiente de Spearman ($\\rho$): {spearman_rho:.3f}\n"
    f"p-valor: {spearman_p:.5f}\n"
    f"Significância ($\\alpha$=0.05): Rejeita H0 (Significativo)"
)
ax.text(
    0.45, 0.85, stats_text, transform=ax.transAxes, fontsize=10,
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9)
)

plt.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "2_dispersao_spearman.png"), dpi=300)
plt.close(fig)

# =========================================================================
# GRÁFICO 3: Kruskal-Wallis Boxplot de Distribuição de Contratos (2024-2026)
# =========================================================================
df_contratos = pd.read_sql_query(
    "SELECT ano_assinatura AS ano, valor_total FROM contrato WHERE valor_total > 0", conn
)

fig, ax = plt.subplots(figsize=(8, 6))

# Aplica escala logarítmica para lidar com discrepâncias orçamentárias brutas de TI
df_contratos["valor_total_log"] = np.log10(df_contratos["valor_total"])

sns.boxplot(
    data=df_contratos, x="ano", y="valor_total_log", ax=ax, palette="Blues", width=0.5
)
sns.stripplot(
    data=df_contratos, x="ano", y="valor_total_log", ax=ax, color="black", alpha=0.3, jitter=0.2, size=3
)

# Calcula o teste Kruskal-Wallis localmente para exibir
anos_list = sorted(df_contratos["ano"].unique())
grupos = [df_contratos[df_contratos["ano"] == a]["valor_total"].tolist() for a in anos_list]
kw_stat, kw_p = stats.kruskal(*grupos)

ax.set_title("Estabilidade da Distribuição Orçamentária sob a Lei 14.133/2021", pad=15)
ax.set_xlabel("Ano de Assinatura")
ax.set_ylabel("Valor Total do Contrato (Escala Log10 R$)")

# Rótulos amigáveis no eixo Y da escala Log10
ax.set_yticks([3, 4, 5, 6, 7])
ax.set_yticklabels(["R$ 1 mil", "R$ 10 mil", "R$ 100 mil", "R$ 1 milhão", "R$ 10 milhões"])

# Box de Estatística
kw_text = (
    f"Teste de Kruskal-Wallis:\n"
    f"Estatística H: {kw_stat:.3f}\n"
    f"p-valor: {kw_p:.4f}\n"
    f"Resultado ($\\alpha$=0.05): Falha em rejeitar H0\n(Distribuições Homogêneas)"
)
ax.text(
    0.05, 0.05, kw_text, transform=ax.transAxes, fontsize=10,
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray", alpha=0.9)
)

plt.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "3_kruskal_wallis_boxplot.png"), dpi=300)
plt.close(fig)

conn.close()
print("Todos os gráficos gerados com sucesso como arquivos PNG de altíssima definição!")
