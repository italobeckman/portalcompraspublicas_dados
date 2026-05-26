# ==============================================================================
# SCRIPT DE AUDITORIA / DEBUG: MAIORES FORNECEDORES E DETALHES DO OLIGOPÓLIO
# Finalidade: Identificar e auditar a dominância de faturamento de estatais de TI 
#             (SERPRO, PRODESP) e desvendar anomalias temporais de monopólio.
# ==============================================================================
import sqlite3
import pandas as pd

DB_PATH = "/home/matheusn/dev/faculdade/portalcompraspublicas_dados/compras_governanca.db"
conn = sqlite3.connect(DB_PATH)

# Load data
query = """
    SELECT ic.*, c.ano_assinatura, c.valor_total AS valor_total_contrato
    FROM item_contrato ic
    JOIN contrato c ON ic.contrato_id = c.id
"""
df = pd.read_sql_query(query, conn)
df["valor_total_item"] = df["valor_unitario"] * df["quantidade"]

CATSER_CODES = {
    "25852": ("Desenvolvimento - Java", "Desenvolvimento"),
    "25860": ("Desenvolvimento - PHP", "Desenvolvimento"),
    "25879": ("Desenvolvimento - .NET", "Desenvolvimento"),
    "25895": ("Desenvolvimento - Web", "Desenvolvimento"),
    "25909": ("Desenvolvimento - Mobile", "Desenvolvimento"),
    "25917": ("Desenvolvimento - Mainframe", "Desenvolvimento"),
    "25925": ("Desenvolvimento - Outras Linguagens", "Desenvolvimento"),
    "25968": ("Manutenção - Java", "Manutenção Evolutiva"),
    "25976": ("Manutenção - PHP", "Manutenção Evolutiva"),
    "25984": ("Manutenção - .NET", "Manutenção Evolutiva"),
    "25992": ("Manutenção - Web", "Manutenção Evolutiva"),
    "26000": ("Manutenção - Mobile", "Manutenção Evolutiva"),
    "26018": ("Manutenção - Mainframe", "Manutenção Evolutiva"),
    "26026": ("Manutenção - Outras Linguagens", "Manutenção Evolutiva"),
}
df["tipo_grupo"] = df["codigo_item"].map(lambda c: CATSER_CODES.get(c, ("", "Outros"))[1])
df = df[df["tipo_grupo"].isin(["Desenvolvimento", "Manutenção Evolutiva"])]

print("=== MAIORES FORNECEDORES DE DESENVOLVIMENTO EM 2025 ===")
df_dev_2025 = df[(df["ano_assinatura"] == 2025) & (df["tipo_grupo"] == "Desenvolvimento")]
forn_2025 = df_dev_2025.groupby("razao_social_fornecedor").agg(
    faturamento=("valor_total_item", "sum"),
    n_contratos=("contrato_id", "nunique")
).reset_index().sort_values(by="faturamento", ascending=False)
forn_2025["share_%"] = (forn_2025["faturamento"] / forn_2025["faturamento"].sum()) * 100
print(forn_2025.head(10).to_string(index=False))

print("\n=== MAIORES FORNECEDORES DE MANUTENÇÃO EVOLUTIVA EM 2025 ===")
df_maint_2025 = df[(df["ano_assinatura"] == 2025) & (df["tipo_grupo"] == "Manutenção Evolutiva")]
forn_maint_2025 = df_maint_2025.groupby("razao_social_fornecedor").agg(
    faturamento=("valor_total_item", "sum"),
    n_contratos=("contrato_id", "nunique")
).reset_index().sort_values(by="faturamento", ascending=False)
forn_maint_2025["share_%"] = (forn_maint_2025["faturamento"] / forn_maint_2025["faturamento"].sum()) * 100
print(forn_maint_2025.head(10).to_string(index=False))

print("\n=== MAIORES FORNECEDORES DE DESENVOLVIMENTO EM 2026 ===")
df_dev_2026 = df[(df["ano_assinatura"] == 2026) & (df["tipo_grupo"] == "Desenvolvimento")]
forn_2026 = df_dev_2026.groupby("razao_social_fornecedor").agg(
    faturamento=("valor_total_item", "sum"),
    n_contratos=("contrato_id", "nunique")
).reset_index().sort_values(by="faturamento", ascending=False)
forn_2026["share_%"] = (forn_2026["faturamento"] / forn_2026["faturamento"].sum()) * 100
print(forn_2026.head(10).to_string(index=False))

print("\n=== DETALHE DA CATEGORIA MOBILE (25909) EM 2026 ===")
df_mobile_2026 = df[(df["ano_assinatura"] == 2026) & (df["codigo_item"] == "25909")]
print(df_mobile_2026[["razao_social_fornecedor", "valor_total_item", "contrato_id"]].to_string(index=False))

conn.close()
