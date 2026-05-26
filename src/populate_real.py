"""
populate_real.py — Extração completa de dados reais da API dadosabertos.compras.gov.br

API Base : https://dadosabertos.compras.gov.br
Endpoint : /modulo-pesquisa-preco/3_consultarServico

NOTA: A documentação Postman lista o parâmetro como 'codigoltemCatalogo' (typo com 'l')
  mas a API de PRODUÇÃO aceita e responde corretamente com 'codigoItemCatalogo' (I maiúsculo).
  Usar o path correto + parâmetro correto resulta em HTTP 200.
"""

import time
import requests
import numpy as np
import pandas as pd
from collections import defaultdict

try:
    from database import (
        SessionLocal, engine,
        OrgaoModel, ContratoModel, ItemContratoModel,
        HistoricoConcentracaoModel, init_db,
    )
except ModuleNotFoundError:
    from src.database import (
        SessionLocal, engine,
        OrgaoModel, ContratoModel, ItemContratoModel,
        HistoricoConcentracaoModel, init_db,
    )

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BASE_URL  = "https://dadosabertos.compras.gov.br"
ANO_INICIO = 2024   # recorte temporal: 2024-2026
# JUSTIFICATIVA: A Lei 14.133/2021 (Nova Lei de Licitações) entrou em vigor pleno
# em 01/04/2023 e revogou definitivamente a Lei 8.666/93 em 30/12/2023.
# Contratos anteriores a 2024 foram celebrados sob regime jurídico distinto,
# criando ruptura estrutural que inviabiliza comparação direta com o período atual.
# O recorte 2024-2026 garante homogeneidade metodológica do corpus de pesquisa.

CATSER_CODES = {
    "25852": ("Desenvolvimento de Novo Software - Java",                              "Desenvolvimento"),
    "25860": ("Desenvolvimento de Novo Software - PHP",                               "Desenvolvimento"),
    "25879": ("Desenvolvimento de Novo Software - .NET, ASP, Delphi, VB ou C++",     "Desenvolvimento"),
    "25895": ("Desenvolvimento de Novo Software - Linguagens Web (Python, Ruby etc)", "Desenvolvimento"),
    "25887": ("Desenvolvimento de Novo Software - Mobile (Android, iOS)",             "Desenvolvimento"),
    "25909": ("Desenvolvimento de Novo Software - Mainframe",                         "Desenvolvimento"),
    "25917": ("Desenvolvimento de Novo Software - Outras Linguagens",                 "Desenvolvimento"),
    "25925": ("Manutenção Evolutiva de Software - Java",                              "Manutenção Evolutiva"),
    "25933": ("Manutenção Evolutiva de Software - PHP",                               "Manutenção Evolutiva"),
    "25941": ("Manutenção Evolutiva de Software - .NET, ASP, Delphi, VB ou C++",     "Manutenção Evolutiva"),
    "25968": ("Manutenção Evolutiva de Software - Linguagens Web (Python, Ruby etc)", "Manutenção Evolutiva"),
    "25950": ("Manutenção Evolutiva de Software - Mobile (Android, iOS)",             "Manutenção Evolutiva"),
    "25976": ("Manutenção Evolutiva de Software - Mainframe",                         "Manutenção Evolutiva"),
    "25984": ("Manutenção Evolutiva de Software - Outras Linguagens",                 "Manutenção Evolutiva"),
}


# ==========================================
# FUNÇÕES DE CONCENTRAÇÃO DE MERCADO
# ==========================================

def calcular_hhi(shares_pct: list) -> float:
    """
    HHI — Herfindahl-Hirschman Index.
    Escala DOJ/OCDE: participações em % (0-100) → HHI de 0 a 10.000.
    Thresholds: <1500 competitivo | 1500-2500 moderado | >2500 concentrado.
    """
    return float(np.sum([s ** 2 for s in shares_pct])) if shares_pct else 0.0


def calcular_cr4(shares_pct: list) -> float:
    """
    CR4 — Razão de Concentração dos 4 maiores fornecedores.
    Retorna valor em % (0-100). Limitado a 100 quando há < 4 players.
    """
    if not shares_pct:
        return 0.0
    return min(float(np.sum(sorted(shares_pct, reverse=True)[:4])), 100.0)


def calcular_gini(valores: list) -> float:
    """Coeficiente de Gini sobre faturamentos (0=igualdade plena, 1=máxima desigualdade)."""
    if not valores or sum(valores) == 0:
        return 0.0
    n = len(valores)
    if n <= 1:
        return 0.0
    vs = sorted(valores)
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * vs) / (n * np.sum(vs))) - (n + 1) / n)


# ==========================================
# EXTRAÇÃO COM PAGINAÇÃO COMPLETA
# ==========================================

def fetch_catser_all_pages(catser_code: str) -> list:
    """
    Extrai TODOS os registros de um CATSER iterando por todas as páginas.

    Parâmetro: 'codigoltemCatalogo' (l minúsculo) — typo da API oficial.
    NÃO usa 'tamanhoPagina' pois não é suportado pelo endpoint.
    """
    url = f"{BASE_URL}/modulo-pesquisa-preco/3_consultarServico"
    todos = []
    pagina = 1

    print(f"  [CATSER {catser_code}] Iniciando extração...")

    while True:
        params = {
            "pagina": pagina,
            "codigoItemCatalogo": int(catser_code),  # I maiúsculo — correto na API de produção
        }

        try:
            resp = requests.get(url, params=params, timeout=20)

            if resp.status_code != 200:
                print(f"  [CATSER {catser_code}] HTTP {resp.status_code} na pág {pagina}. Abortando.")
                break

            data = resp.json()
            resultados = data.get("resultado", [])

            if not resultados:
                print(f"  [CATSER {catser_code}] Sem resultados na pág {pagina}. Fim.")
                break

            todos.extend(resultados)
            pags_restantes = int(data.get("paginasRestantes", 0))
            total_pags     = int(data.get("totalPaginas", 1))
            total_regs     = int(data.get("totalRegistros", len(todos)))

            print(f"  [CATSER {catser_code}] Pág {pagina}/{total_pags} "
                  f"| +{len(resultados)} itens | total={len(todos)}/{total_regs}")

            if pags_restantes <= 0:
                break

            pagina += 1
            time.sleep(0.3)  # cortesia entre páginas

        except requests.exceptions.Timeout:
            print(f"  [CATSER {catser_code}] Timeout na pág {pagina}. Aguardando 2s...")
            time.sleep(2.0)
            pagina += 1
        except Exception as exc:
            print(f"  [CATSER {catser_code}] Erro inesperado na pág {pagina}: {exc}")
            break

    print(f"  [CATSER {catser_code}] Finalizado: {len(todos)} registros.\n")
    return todos


# ==========================================
# POPULAÇÃO PRINCIPAL
# ==========================================

def popular_banco_real():
    session = SessionLocal()

    try:
        # ── FASE 0: Limpeza ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("FASE 0: Limpando banco de dados...")
        print("=" * 60)
        session.query(HistoricoConcentracaoModel).delete()
        session.query(ItemContratoModel).delete()
        session.query(ContratoModel).delete()
        session.query(OrgaoModel).delete()
        session.commit()
        print("Banco limpo.\n")

        # ── FASE 1: Coleta com deduplicação por idItemCompra ───────
        print("=" * 60)
        print("FASE 1: Coletando dados de todos os 14 CATSERs...")
        print("=" * 60)

        # Deduplicação: mesmo idItemCompra pode aparecer em queries de CATSERs distintos
        itens_por_id: dict = {}   # idItemCompra -> item (com _catser_* injetados)
        itens_sem_id: list = []   # itens sem idItemCompra

        for catser_code, (catser_desc, catser_grupo) in CATSER_CODES.items():
            registros = fetch_catser_all_pages(catser_code)
            for item in registros:
                item["_catser_code"]  = catser_code
                item["_catser_desc"]  = catser_desc
                item["_catser_grupo"] = catser_grupo

                id_item = item.get("idItemCompra")
                if id_item is not None:
                    if id_item not in itens_por_id:
                        itens_por_id[id_item] = item
                else:
                    itens_sem_id.append(item)

            time.sleep(1.0)  # cortesia entre CATSERs

        todos_itens = list(itens_por_id.values()) + itens_sem_id
        print(f"\nTotal de itens únicos coletados: {len(todos_itens)}\n")

        # ── FASE 2: Filtro temporal e agrupamento por contrato ─────
        print("=" * 60)
        print(f"FASE 2: Filtrando >= {ANO_INICIO} e agrupando por contrato (idCompra)...")
        print("=" * 60)

        # Agrupa itens por idCompra para calcular valor_total real do contrato
        contratos: dict = defaultdict(lambda: {"meta": None, "itens": []})
        descartados = 0
        _seq = 0  # contador para contratos sem idCompra

        for item in todos_itens:
            data_str = item.get("dataCompra") or "2000-01-01"
            try:
                ano = int(str(data_str)[:4])
            except (ValueError, TypeError):
                ano = 2000

            if ano < ANO_INICIO:
                descartados += 1
                continue

            id_compra = item.get("idCompra")
            if not id_compra:
                _seq += 1
                id_compra = f"SEM_ID_{_seq}"

            if contratos[id_compra]["meta"] is None:
                contratos[id_compra]["meta"] = {
                    "id_compra":     id_compra,
                    "ano":           ano,
                    "codigo_orgao":  str(item.get("codigoOrgao") or "0"),
                    "nome_orgao":    item.get("nomeOrgao") or "Órgão Não Informado",
                }
            contratos[id_compra]["itens"].append(item)

        print(f"Contratos únicos: {len(contratos)} | Itens descartados (< {ANO_INICIO}): {descartados}\n")

        # ── FASE 3: Persistência ───────────────────────────────────
        print("=" * 60)
        print("FASE 3: Persistindo órgãos, contratos e itens...")
        print("=" * 60)

        orgaos_cache: dict = {}   # codigo_orgao -> OrgaoModel
        total_itens_salvos = 0

        for id_compra, contrato_data in contratos.items():
            meta  = contrato_data["meta"]
            itens = contrato_data["itens"]

            # 3a. Órgão
            cod_orgao  = meta["codigo_orgao"]
            nome_orgao = meta["nome_orgao"]

            if cod_orgao not in orgaos_cache:
                db_orgao = session.query(OrgaoModel).filter(
                    OrgaoModel.codigo_orgao == cod_orgao
                ).first()
                if not db_orgao:
                    db_orgao = OrgaoModel(codigo_orgao=cod_orgao, razao_social=nome_orgao)
                    session.add(db_orgao)
                    session.flush()
                orgaos_cache[cod_orgao] = db_orgao

            db_orgao = orgaos_cache[cod_orgao]

            # 3b. Contrato — valor_total = soma real de todos os itens
            valor_total = sum(
                (float(i.get("quantidade")) if i.get("quantidade") is not None else 0.0)
                * (float(i.get("precoUnitario")) if i.get("precoUnitario") is not None else 0.0)
                for i in itens
            )

            # Evita duplicata se o mesmo idCompra já foi inserido
            db_contrato = session.query(ContratoModel).filter(
                ContratoModel.numero_contrato == id_compra
            ).first()

            if not db_contrato:
                db_contrato = ContratoModel(
                    numero_contrato=id_compra,
                    ano_assinatura=meta["ano"],
                    valor_total=valor_total,
                    orgao_id=db_orgao.id,
                )
                session.add(db_contrato)
                session.flush()

            # 3c. Itens — capturando todos os campos da API
            for item in itens:
                qtd        = float(item.get("quantidade"))  if item.get("quantidade")   is not None else 0.0
                preco_unit = float(item.get("precoUnitario")) if item.get("precoUnitario") is not None else 0.0

                ni_forn = str(item.get("niFornecedor") or "00000000000000")
                ni_forn = "".join(filter(str.isdigit, ni_forn)).zfill(14)[:14]

                db_item = ItemContratoModel(
                    id_item_compra          = item.get("idItemCompra"),
                    codigo_item             = item["_catser_code"],
                    descricao               = item.get("descricaoItem") or item["_catser_desc"],
                    valor_unitario          = preco_unit,
                    quantidade              = int(qtd) if qtd != int(qtd) else int(qtd),
                    nome_unidade_medida     = item.get("nomeUnidadeMedida"),
                    sigla_unidade_medida    = item.get("siglaUnidadeMedida"),
                    cnpj_fornecedor         = ni_forn,
                    razao_social_fornecedor = item.get("nomeFornecedor") or "Fornecedor Não Informado",
                    forma                   = item.get("forma"),
                    modalidade              = item.get("modalidade"),
                    criterio_julgamento     = item.get("criterioJulgamento"),
                    estado                  = item.get("estado"),
                    municipio               = item.get("municipio"),
                    codigo_municipio        = item.get("codigoMunicipio"),
                    esfera                  = item.get("esfera"),
                    poder                   = item.get("poder"),
                    codigo_uasg             = str(item.get("codigoUasg")) if item.get("codigoUasg") else None,
                    nome_uasg               = item.get("nomeUasg"),
                    contrato_id             = db_contrato.id,
                )
                session.add(db_item)
                total_itens_salvos += 1

            session.commit()

        print(f"Persistência concluída: {len(contratos)} contratos | {total_itens_salvos} itens.\n")

        # ── FASE 4: Cálculo dos índices de concentração ────────────
        print("=" * 60)
        print("FASE 4: Calculando HHI, CR4 e Gini por CATSER/ano...")
        print("=" * 60)

        query_sql = """
            SELECT ic.codigo_item, ic.cnpj_fornecedor,
                   ic.valor_unitario, ic.quantidade, c.ano_assinatura
            FROM item_contrato ic
            JOIN contrato c ON ic.contrato_id = c.id
        """
        # Fix #12: usa engine diretamente (session.bind depreciado no SQLAlchemy 2.x)
        df = pd.read_sql(query_sql, engine)
        df["valor_total_item"] = df["valor_unitario"] * df["quantidade"]

        if df.empty:
            print("Nenhum dado para calcular indicadores. Abortando Fase 4.")
        else:
            for ano in sorted(df["ano_assinatura"].unique()):
                for catser_code, (catser_desc, catser_grupo) in CATSER_CODES.items():
                    df_f = df[(df["ano_assinatura"] == ano) & (df["codigo_item"] == catser_code)]
                    if df_f.empty:
                        continue

                    fat_forn    = df_f.groupby("cnpj_fornecedor")["valor_total_item"].sum()
                    total_mkt   = fat_forn.sum()
                    if total_mkt == 0:
                        continue

                    shares_pct = (fat_forn / total_mkt * 100).tolist()

                    db_conc = HistoricoConcentracaoModel(
                        ano                       = int(ano),
                        codigo_catser             = catser_code,
                        descricao_catser          = catser_desc,
                        tipo_grupo                = catser_grupo,
                        faturamento_total_mercado = float(total_mkt),
                        hhi                       = round(calcular_hhi(shares_pct), 2),
                        cr4                       = round(calcular_cr4(shares_pct), 2),
                        gini                      = round(calcular_gini(fat_forn.tolist()), 3),
                        total_fornecedores        = len(fat_forn),
                    )
                    session.add(db_conc)

            session.commit()
            print("Indicadores analíticos gravados com sucesso.\n")

    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    popular_banco_real()
    print("=" * 60)
    print("Processamento de dados reais do Compras.gov.br concluído!")
    print("=" * 60)
