# ==============================================================================
# SCRIPT DE AUDITORIA / DEBUG: ANÁLISE DE VIÉS DO HHI (SIMPLES VS PONDERADO)
# Finalidade: Investigar o viés estatístico da média simples de HHI que estava
#             superestimando a concentração de mercado de Fábrica de Software.
# ==============================================================================
import os
import sqlite3
import pandas as pd
import numpy as np

# Database path -- TROCAR CASO DESEJA FAZER O TESTE
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

# Calculate HHI per CATSER and Year
catser_data = []
for (ano, grupo, catser), group in df.groupby(["ano_assinatura", "tipo_grupo", "codigo_item"]):
    fat_forn = group.groupby("cnpj_fornecedor")["valor_total_item"].sum()
    mkt_total = fat_forn.sum()
    n_fornecedores = fat_forn.nunique()
    if mkt_total > 0:
        shares = (fat_forn / mkt_total * 100).tolist()
        hhi = sum(s ** 2 for s in shares)
        catser_data.append({
            "ano": ano,
            "tipo_grupo": grupo,
            "catser": catser,
            "faturamento": mkt_total,
            "hhi": hhi,
            "n_fornecedores": n_fornecedores,
            "n_contratos": len(group)
        })

df_catser = pd.DataFrame(catser_data)

print("=== HHI E VALORES POR CATSER EM 2026 ===")
df_2026 = df_catser[df_catser["ano"] == 2026].sort_values(by="faturamento", ascending=False)
print(df_2026.to_string(index=False))

print("\n=== COMPARAÇÃO DE MÉDIAS DE HHI POR GRUPO E ANO ===")
for (ano, grupo), g in df_catser.groupby(["ano", "tipo_grupo"]):
    simple_mean = g["hhi"].mean()
    weighted_mean = np.average(g["hhi"], weights=g["faturamento"])
    total_fat = g["faturamento"].sum()
    print(f"Ano: {ano} | Grupo: {grupo:<20} | Faturamento Total: R$ {total_fat/1e6:7.2f}M | HHI Simples: {simple_mean:7.1f} | HHI Ponderado: {weighted_mean:7.1f}")

conn.close()
