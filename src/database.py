import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Configuração do Banco de Dados SQLite local
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compras_governanca.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 1. MODELOS DE BANCO DE DADOS (SQLAlchemy ORM)
# ==========================================

class OrgaoModel(Base):
    """
    Representa o órgão comprador (Unidade Gestora / Órgão Superior).
    NOTA: codigo_orgao = campo 'codigoOrgao' da API dadosabertos.compras.gov.br
    (código SIORG/SIASG do órgão — NÃO é CNPJ).
    """
    __tablename__ = "orgao"

    id              = Column(Integer, primary_key=True, index=True)
    codigo_orgao    = Column(String(20), unique=True, nullable=False, index=True)  # codigoOrgao da API
    razao_social    = Column(String(255), nullable=False)

    contratos = relationship("ContratoModel", back_populates="orgao")


class ContratoModel(Base):
    """
    Representa um processo de compra (idCompra) da API compras.gov.br.
    Valor total = soma de todos os itens do processo.
    """
    __tablename__ = "contrato"
    __table_args__ = (
        UniqueConstraint("numero_contrato", name="uq_numero_contrato"),
    )

    id               = Column(Integer, primary_key=True, index=True)
    numero_contrato  = Column(String(100), nullable=False, unique=True)  # idCompra da API
    ano_assinatura   = Column(Integer, nullable=False, index=True)
    valor_total      = Column(Float, nullable=False)   # soma(qtd * precoUnitario) de todos os itens
    orgao_id         = Column(Integer, ForeignKey("orgao.id"), nullable=False)

    orgao  = relationship("OrgaoModel", back_populates="contratos")
    itens  = relationship("ItemContratoModel", back_populates="contrato", cascade="all, delete-orphan")


class ItemContratoModel(Base):
    """
    Representa um item licitado dentro de um processo de compra.
    Campos capturados diretamente da API dadosabertos.compras.gov.br
    endpoint: /modulo-pesquisa-preco/3_consultarServico
    """
    __tablename__ = "item_contrato"

    id                       = Column(Integer, primary_key=True, index=True)
    id_item_compra           = Column(Integer, nullable=True, index=True)   # idItemCompra da API
    codigo_item              = Column(String(30), nullable=False, index=True) # codigoItemCatalogo (CATSER)
    descricao                = Column(String(500), nullable=True)
    grupo_tic                = Column(Integer, nullable=False, default=58)
    # Preço e quantidade
    valor_unitario           = Column(Float, nullable=False)
    quantidade               = Column(Integer, nullable=False)
    nome_unidade_medida      = Column(String(100), nullable=True)
    sigla_unidade_medida     = Column(String(20), nullable=True)
    # Fornecedor
    cnpj_fornecedor          = Column(String(20), nullable=False, index=True)  # niFornecedor da API
    razao_social_fornecedor  = Column(String(255), nullable=False)
    # Modalidade e critério (NOVO)
    forma                    = Column(String(100), nullable=True)
    modalidade               = Column(Integer, nullable=True)
    criterio_julgamento      = Column(String(100), nullable=True)
    # Georreferenciamento (NOVO)
    estado                   = Column(String(2), nullable=True)
    municipio                = Column(String(100), nullable=True)
    codigo_municipio         = Column(Integer, nullable=True)
    # Esfera e poder (NOVO)
    esfera                   = Column(String(50), nullable=True)
    poder                    = Column(String(50), nullable=True)
    # UASG (unidade compradora, distinta do órgão superior) (NOVO)
    codigo_uasg              = Column(String(20), nullable=True)
    nome_uasg                = Column(String(255), nullable=True)

    contrato_id = Column(Integer, ForeignKey("contrato.id"), nullable=False)
    contrato    = relationship("ContratoModel", back_populates="itens")


class HistoricoConcentracaoModel(Base):
    """
    Tabela analítica pré-calculada de HHI, CR4, Gini e volume financeiro anual por CATSER.
    HHI usa escala 0–10.000 (participações em %, padrão DOJ/OCDE).
    Thresholds: < 1.500 competitivo | 1.500–2.500 moderado | > 2.500 concentrado.
    """
    __tablename__ = "historico_concentracao"

    id                       = Column(Integer, primary_key=True, index=True)
    ano                      = Column(Integer, nullable=False, index=True)
    codigo_catser            = Column(String(30), nullable=False, index=True)
    descricao_catser         = Column(String(255), nullable=False)
    tipo_grupo               = Column(String(50), nullable=False)
    faturamento_total_mercado = Column(Float, nullable=False)
    hhi                      = Column(Float, nullable=False)  # escala 0-10.000
    cr4                      = Column(Float, nullable=False)  # escala 0-100 (%)
    gini                     = Column(Float, nullable=False)  # escala 0-1
    total_fornecedores       = Column(Integer, nullable=False)


# ==========================================
# 2. SCHEMAS DE VALIDAÇÃO (Pydantic v2) — para a API local POST
# ==========================================

class ItemContratoSchema(BaseModel):
    codigo_item: str             = Field(..., alias="codigoItem")
    descricao: Optional[str]     = Field(None, alias="descricaoItem")
    grupo_tic: int               = Field(58, alias="grupoTic")
    valor_unitario: float        = Field(..., alias="valorUnitario")
    quantidade: int              = Field(..., alias="quantidadeItem")
    cnpj_fornecedor: str         = Field(..., alias="cnpjFornecedor")
    razao_social_fornecedor: str = Field(..., alias="razaoSocialFornecedor")

    @field_validator("cnpj_fornecedor")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        clean = "".join(filter(str.isdigit, v))
        if len(clean) not in (11, 14):
            raise ValueError("niFornecedor deve ter 11 (CPF) ou 14 (CNPJ) dígitos.")
        return clean.zfill(14)


class ContratoSchema(BaseModel):
    numero_contrato: str          = Field(..., alias="numeroContrato")
    ano_assinatura: int           = Field(..., alias="ano")
    valor_total: float            = Field(..., alias="valorTotal")
    codigo_orgao: str             = Field(..., alias="codigoOrgao")
    razao_social_orgao: str       = Field(..., alias="razaoSocialOrgao")
    itens: List[ItemContratoSchema]


# ==========================================
# 3. INICIALIZAÇÃO
# ==========================================

def init_db():
    """Cria as tabelas SQLite se ainda não existirem."""
    print(f"Inicializando banco de dados em: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")


def get_db():
    """Dependency de sessão para o FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
