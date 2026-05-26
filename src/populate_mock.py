import random
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
try:
    from database import (
        SessionLocal,
        OrgaoModel,
        ContratoModel,
        ItemContratoModel,
        HistoricoConcentracaoModel,
        init_db
    )
except ModuleNotFoundError:
    from src.database import (
        SessionLocal,
        OrgaoModel,
        ContratoModel,
        ItemContratoModel,
        HistoricoConcentracaoModel,
        init_db
    )

# Definição dos 14 CATSERs de Fábrica de Software
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

# Pool de Órgãos Públicos (UGs)
ORGAOS = [
    ("Ministério da Gestão e Inovação em Serviços Públicos - MGI", "00348001000180"),
    ("Ministério da Educação - MEC", "00348002000190"),
    ("Ministério da Saúde - MS", "00348003000101"),
    ("Ministério da Ciência, Tecnologia e Inovação - MCTI", "00348004000110"),
    ("Tribunal de Contas da União - TCU", "00348005000120"),
    ("Dataprev - Tecnologia e Informações da Previdência Social", "00348006000130"),
    ("Serpro - Serviço Federal de Processamento de Dados", "00348007000140"),
    ("Ministério da Fazenda - MF", "00348008000150")
]

# Pool de Fornecedores de Fábrica de Software
FORNECEDORES = [
    # Grandes corporações tradicionais
    ("Stefanini Consultoria e Assessoria em Informática S.A.", "11111111000111"),
    ("TIVIT Terceirização de Processos, Serviços e Tecnologia S.A.", "22222222000122"),
    ("Cast Informática S.A.", "33333333000133"),
    ("Resource Tecnologia e Sistemas de Informação Ltda", "44444444000144"),
    ("Accenture do Brasil Ltda", "55555555000155"),
    
    # Especializadas em Mainframe / Governo
    ("IBM Brasil Indústria Máquinas e Serviços Ltda", "66666666000166"),
    ("Unisys Brasil Ltda", "77777777000177"),
    
    # Consultorias Web / Ágeis / Inovação
    ("Concrete Solutions Tecnologia da Informação S.A.", "88888888000188"),
    ("DTI Digital Ltda", "99999999000199"),
    ("Zup IT Serviços em Tecnologia da Informação Ltda", "12121212000112"),
    ("CI&T Software S.A.", "13131313000113"),
    ("Sensedia Tecnologia e Sistemas S.A.", "14141414000114"),
    
    # Pequenas/Médias Empresas locais (long-tail)
    ("Alfa Sistemas de Computação Ltda", "15151515000115"),
    ("Beta Desenvolvimento de Software Ltda", "16161616000116"),
    ("Gama Tech Consultoria em TI Ltda", "17171717000117"),
    ("Omega Softwares Web Eireli", "18181818000118")
]

def calcular_hhi(shares: list) -> float:
    """Calcula HHI a partir de uma lista de market shares percentuais (0 a 100)."""
    return float(np.sum([s ** 2 for s in shares]))

def calcular_cr4(shares: list) -> float:
    """Calcula CR4 a partir de uma lista de market shares (ordenada decrescentemente)."""
    sorted_shares = sorted(shares, reverse=True)
    return float(np.sum(sorted_shares[:4]))

def calcular_gini(values: list) -> float:
    """Calcula Coeficiente de Gini para desigualdade de valores contratuais."""
    if not values or sum(values) == 0:
        return 0.0
    n = len(values)
    values_sorted = sorted(values)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * values_sorted) / (n * np.sum(values_sorted))) - (n + 1) / n)

def popular_banco():
    session = SessionLocal()
    
    print("Limpando dados antigos...")
    session.query(ItemContratoModel).delete()
    session.query(ContratoModel).delete()
    session.query(OrgaoModel).delete()
    session.query(HistoricoConcentracaoModel).delete()
    session.commit()
    
    print("Injetando Órgãos Licitantes...")
    db_orgaos = []
    for razao, cnpj in ORGAOS:
        o = OrgaoModel(cnpj=cnpj, razao_social=razao)
        session.add(o)
        db_orgaos.append(o)
    session.commit()
    
    # Mapearemos a simulação de 2022 a 2025 para gerar os contratos
    anos = [2022, 2023, 2024, 2025]
    
    print("Gerando Contratos e Itens de Fábrica de Software...")
    contrato_idx = 1
    
    for ano in anos:
        for catser_code, (catser_desc, catser_grupo) in CATSER_CODES.items():
            
            # Vamos gerar faturamentos totais diferentes dependendo do CATSER e do ano
            # Stacks tradicionais como Java e .NET movimentam mais dinheiro
            if "Java" in catser_desc or ".NET" in catser_desc:
                financeiro_base = random.uniform(15_000_000, 30_000_000)
            elif "Mainframe" in catser_desc:
                financeiro_base = random.uniform(8_000_000, 15_000_000)
            elif "Linguagens Web" in catser_desc or "Mobile" in catser_desc:
                financeiro_base = random.uniform(10_000_000, 20_000_000)
            else:
                financeiro_base = random.uniform(5_000_000, 10_000_000)
                
            # Inflação/aumento de gastos com o passar dos anos
            financeiro_ano = financeiro_base * (1.1 ** (ano - 2022))
            
            # Modelar os perfis de concentração de fornecedores!
            shares_simulados = []
            
            # Padrão A: Monopólio/Oligopólio Rígido em Mainframe (IBM e Unisys dominam > 80% do mercado)
            if "Mainframe" in catser_desc:
                fornecedores_ativos = FORNECEDORES[5:7] # IBM e Unisys
                long_tail = FORNECEDORES[0:1] # Adiciona apenas uma empresa de controle
                todas = fornecedores_ativos + long_tail
                
                # IBM pega 65%, Unisys pega 30%, outra pega 5%
                shares_simulados = [65.0, 30.0, 5.0]
                
            # Padrão B: Greenfield vs. Brownfield (Manutenção Evolutiva é mais concentrada do que Desenvolvimento)
            elif catser_grupo == "Manutenção Evolutiva":
                # Apenas as 4 grandes dominam a manutenção legada (lock-in)
                todas = FORNECEDORES[0:4] + FORNECEDORES[12:14]
                # Cast, Stefanini, Tivit e Resource concentram 85% do mercado
                shares_simulados = [35.0, 25.0, 15.0, 10.0, 10.0, 5.0]
                
            # Padrão C: Desenvolvimento Web/Mobile é altamente concorrencial e descentralizado
            elif "Linguagens Web" in catser_desc or "Mobile" in catser_desc:
                # pulverizado entre as agências de inovação e empresas médias
                todas = FORNECEDORES[7:16]
                # 9 empresas ativas dividem igualmente
                shares_simulados = [random.uniform(5, 15) for _ in todas]
                # Normaliza shares para somar 100%
                s_sum = sum(shares_simulados)
                shares_simulados = [(s / s_sum) * 100 for s in shares_simulados]
                
            # Padrão D: Java / .NET Desenvolvimento corporativo - oligopólio moderado
            else:
                todas = FORNECEDORES[0:6] + FORNECEDORES[10:12]
                shares_simulados = [random.uniform(5, 30) for _ in range(5)]
                # Normaliza shares
                s_sum = sum(shares_simulados)
                shares_simulados = [(s / s_sum) * 100 for s in shares_simulados]
            
            # Assegurar correspondência entre shares e fornecedores
            for idx, share in enumerate(shares_simulados):
                if idx >= len(todas):
                    break
                fornecedor_razao, fornecedor_cnpj = todas[idx]
                valor_faturado_empresa = financeiro_ano * (share / 100)
                
                # Criar Contrato no banco SQLite
                # Escolhe um órgão comprador aleatório
                orgao_comprador = random.choice(db_orgaos)
                
                # Cria contrato
                num_contrato = f"{contrato_idx:04d}/{ano}"
                db_contrato = ContratoModel(
                    numero_contrato=num_contrato,
                    ano_assinatura=ano,
                    valor_total=valor_faturado_empresa,
                    orgao=orgao_comprador
                )
                session.add(db_contrato)
                
                # Cria item vinculando o código CATSER
                db_item = ItemContratoModel(
                    codigo_item=catser_code,
                    descricao=catser_desc,
                    grupo_tic=58,
                    valor_unitario=valor_faturado_empresa / 12, # valor mensal
                    quantidade=12,
                    cnpj_fornecedor=fornecedor_cnpj,
                    razao_social_fornecedor=fornecedor_razao,
                    contrato=db_contrato
                )
                session.add(db_item)
                contrato_idx += 1
                
    session.commit()
    print("Contratos salvos. Iniciando pré-cálculo dos Indicadores Analíticos (HHI, CR4, Gini)...")
    
    # ===============================================================
    # 4. LEITURA VIA PANDAS DO BANCO LOCAL PARA COMPUTAR HISTÓRICO
    # ===============================================================
    query_itens = """
        SELECT ic.codigo_item, ic.cnpj_fornecedor, ic.valor_unitario, ic.quantidade, c.ano_assinatura
        FROM item_contrato ic
        JOIN contrato c ON ic.contrato_id = c.id
    """
    df_itens = pd.read_sql(query_itens, SessionLocal().bind)
    df_itens['valor_total_item'] = df_itens['valor_unitario'] * df_itens['quantidade']
    
    for ano in anos:
        for catser_code, (catser_desc, catser_grupo) in CATSER_CODES.items():
            df_filtro = df_itens[(df_itens['ano_assinatura'] == ano) & (df_itens['codigo_item'] == catser_code)]
            
            if df_filtro.empty:
                continue
                
            faturamento_fornecedores = df_filtro.groupby('cnpj_fornecedor')['valor_total_item'].sum()
            valor_total_mercado = faturamento_fornecedores.sum()
            
            if valor_total_mercado == 0:
                continue
                
            market_share = (faturamento_fornecedores / valor_total_mercado) * 100
            
            hhi = calcular_hhi(market_share.tolist())
            cr4 = calcular_cr4(market_share.tolist())
            gini = calcular_gini(faturamento_fornecedores.tolist())
            total_fornecedores = len(faturamento_fornecedores)
            
            db_concentracao = HistoricoConcentracaoModel(
                ano=ano,
                codigo_catser=catser_code,
                descricao_catser=catser_desc,
                tipo_grupo=catser_grupo,
                faturamento_total_mercado=float(valor_total_mercado),
                hhi=round(hhi, 2),
                cr4=round(cr4, 2),
                gini=round(gini, 3),
                total_fornecedores=total_fornecedores
            )
            session.add(db_concentracao)
            
    session.commit()
    print("Pré-cálculos analíticos populados e gravados com sucesso!")
    session.close()

if __name__ == "__main__":
    init_db()
    popular_banco()
    print("Injeção de dados simulados de Fábrica de Software concluída!")
