import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from scipy import stats

try:
    from database import (
        get_db, engine,
        OrgaoModel, ContratoModel, ItemContratoModel, HistoricoConcentracaoModel,
    )
except ModuleNotFoundError:
    from src.database import (
        get_db, engine,
        OrgaoModel, ContratoModel, ItemContratoModel, HistoricoConcentracaoModel,
    )

app = FastAPI(
    title="API de Governança de TI — Fábrica de Software",
    description=(
        "API local para análise de dados de compras públicas (dadosabertos.compras.gov.br). "
        "Consulte faturamentos, HHI, CR4, Gini e testes estatísticos (Spearman, Kruskal-Wallis) "
        "sobre os 14 códigos CATSER de Fábrica de Software."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "Online",
        "versao": "2.0.0",
        "fonte_dados": "dadosabertos.compras.gov.br",
        "endpoints": {
            "/api/v1/contratos":           "Listar contratos de Fábrica de Software",
            "/api/v1/analise/hhi":         "HHI, CR4 e Gini por CATSER/ano",
            "/api/v1/analise/estatisticas":"Spearman e Kruskal-Wallis",
        },
    }


@app.get("/api/v1/contratos")
def listar_contratos(
    ano: Optional[int]          = Query(None, description="Filtrar por ano de assinatura"),
    codigo_catser: Optional[str] = Query(None, description="Filtrar por código CATSER"),
    estado: Optional[str]        = Query(None, description="Filtrar por UF (ex: SP, DF)"),
    db: Session                  = Depends(get_db),
):
    """Retorna contratos com seus itens de software."""
    query = db.query(ContratoModel).join(ItemContratoModel)

    if ano:
        query = query.filter(ContratoModel.ano_assinatura == ano)
    if codigo_catser:
        query = query.filter(ItemContratoModel.codigo_item == codigo_catser)
    if estado:
        query = query.filter(ItemContratoModel.estado == estado.upper())

    contratos = query.distinct().all()

    return [
        {
            "id":               c.id,
            "numero_contrato":  c.numero_contrato,
            "ano_assinatura":   c.ano_assinatura,
            "valor_total":      c.valor_total,
            "orgao": {
                "codigo_orgao": c.orgao.codigo_orgao,
                "razao_social": c.orgao.razao_social,
            },
            "itens": [
                {
                    "id_item_compra":           item.id_item_compra,
                    "codigo_catser":            item.codigo_item,
                    "descricao":                item.descricao,
                    "modalidade":               item.modalidade,
                    "criterio_julgamento":      item.criterio_julgamento,
                    "forma":                    item.forma,
                    "quantidade":               item.quantidade,
                    "valor_unitario":           item.valor_unitario,
                    "nome_unidade_medida":      item.nome_unidade_medida,
                    "estado":                   item.estado,
                    "municipio":                item.municipio,
                    "esfera":                   item.esfera,
                    "poder":                    item.poder,
                    "codigo_uasg":              item.codigo_uasg,
                    "nome_uasg":                item.nome_uasg,
                    "fornecedor": {
                        "ni_fornecedor":  item.cnpj_fornecedor,
                        "razao_social":   item.razao_social_fornecedor,
                    },
                }
                for item in c.itens
            ],
        }
        for c in contratos
    ]


@app.get("/api/v1/analise/hhi")
def obter_hhi_historico(
    ano: Optional[int]        = Query(None, description="Filtrar ano específico"),
    tipo_grupo: Optional[str] = Query(None, description="'Desenvolvimento' ou 'Manutenção Evolutiva'"),
    db: Session               = Depends(get_db),
):
    """
    Evolução histórica dos índices HHI, CR4 e Gini por CATSER.
    HHI na escala 0–10.000 (DOJ/OCDE — participações em %).
    """
    query = db.query(HistoricoConcentracaoModel)
    if ano:
        query = query.filter(HistoricoConcentracaoModel.ano == ano)
    if tipo_grupo:
        query = query.filter(HistoricoConcentracaoModel.tipo_grupo == tipo_grupo)

    return [
        {
            "ano":                      r.ano,
            "codigo_catser":            r.codigo_catser,
            "descricao_catser":         r.descricao_catser,
            "tipo_grupo":               r.tipo_grupo,
            "faturamento_total_mercado": r.faturamento_total_mercado,
            "HHI":  r.hhi,
            "CR4":  r.cr4,
            "Gini": r.gini,
            "total_fornecedores":       r.total_fornecedores,
            "classificacao_concentracao": (
                "Altamente Concentrado (Risco Crítico)"  if r.hhi > 2500
                else "Moderadamente Concentrado"         if r.hhi >= 1500
                else "Competitivo (Baixo Risco)"
            ),
        }
        for r in query.all()
    ]


@app.get("/api/v1/analise/estatisticas")
def calcular_estatisticas(db: Session = Depends(get_db)):
    """
    Testes estatísticos não-paramétricos:
    - Spearman: correlação entre faturamento total do CATSER e HHI.
    - Kruskal-Wallis: variação anual dos valores contratuais.
    """
    historico = db.query(HistoricoConcentracaoModel).all()
    if not historico:
        raise HTTPException(
            status_code=404,
            detail="Sem dados analíticos. Execute: make db-real ou make db-mock",
        )

    df_hhi = pd.DataFrame([
        {"faturamento": r.faturamento_total_mercado, "hhi": r.hhi}
        for r in historico
    ])
    spearman_rho, spearman_p = stats.spearmanr(df_hhi["faturamento"], df_hhi["hhi"])

    # Fix #12: usa engine diretamente (session.bind depreciado no SQLAlchemy 2.x)
    df_contratos = pd.read_sql(
        "SELECT ano_assinatura AS ano, valor_total AS valor FROM contrato",
        engine,
    )

    anos = sorted(df_contratos["ano"].unique())
    grupos = [df_contratos[df_contratos["ano"] == a]["valor"].dropna().tolist() for a in anos]

    kw_stat, kw_p = (0.0, 1.0)
    if len(grupos) > 1:
        kw_stat, kw_p = stats.kruskal(*grupos)

    return {
        "teste_spearman": {
            "hipotese_nula":              "Não há correlação entre faturamento do CATSER e HHI.",
            "coeficiente_rho":            round(float(spearman_rho), 4),
            "p_valor":                    float(spearman_p),
            "significativo_alpha_0_05":   bool(spearman_p < 0.05),
            "interpretacao": (
                "Rejeita-se H0: volume licitado correlaciona-se com concentração de mercado."
                if spearman_p < 0.05
                else "Falha em rejeitar H0: sem correlação sistemática."
            ),
        },
        "teste_kruskal_wallis": {
            "hipotese_nula":            "Distribuições de faturamento são idênticas entre os anos.",
            "anos_comparados":          [int(a) for a in anos],
            "estatistica_H":            round(float(kw_stat), 4),
            "p_valor":                  float(kw_p),
            "significativo_alpha_0_05": bool(kw_p < 0.05),
            "interpretacao": (
                "Rejeita-se H0: variação estrutural significativa no orçamento entre os anos."
                if kw_p < 0.05
                else "Falha em rejeitar H0: sem variação significativa entre os anos."
            ),
        },
    }
