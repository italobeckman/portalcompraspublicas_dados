# ==========================================
# MAKEFILE DE GOVERNANÇA DE TI & API LOCAL
# ==========================================
# Facilita a instalação, população de dados, execução da API e exportação de documentação acadêmica.

.PHONY: help install db-real db-mock run docs stats dashboard clean

# Target padrão: exibe o menu de ajuda
help:
	@echo "========================================================================="
	@echo "             Comandos do Projeto - Governança de TI Fábrica de Software  "
	@echo "========================================================================="
	@echo "  make install         Instala as dependências necessárias (fastapi, pandas, scipy, etc.)"
	@echo "  make db-real         Limpa e carrega dados 100% REAIS da API Compras.gov.br (850+ itens)"
	@echo "  make db-mock         Limpa e carrega massa de testes sintética (2022-2025)"
	@echo "  make run             Inicia o servidor de API local em http://127.0.0.1:8000"
	@echo "  make docs            Exporta a documentação OpenAPI 3.0 para o arquivo 'api_docs.json'"
	@echo "  make stats           Consulta e exibe os resultados dos testes estatísticos reais"
	@echo "  make clean           Remove o banco de dados local SQLite e arquivos temporários de docs"
	@echo "========================================================================="

# Instalação automatizada das dependências (incluindo dashboard e estatística)
install:
	@echo "Instalando dependências do projeto..."
	pip install fastapi uvicorn sqlalchemy pydantic scipy pandas requests matplotlib seaborn streamlit plotly

# Carga de dados reais — recorte temporal 2024-2026 (pós-Lei 14.133/2021)
db-real:
	@echo "Carregando dados verídicos e históricos da API pública oficial..."
	python src/populate_real.py

# Carga de dados mockados (para testes/simulação controlada)
db-mock:
	@echo "Carregando dados sintéticos estruturados..."
	python src/populate_mock.py

# Inicializa o servidor FastAPI local
run:
	@echo "Iniciando servidor de API FastAPI local..."
	python -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload

# Inicializa o painel interativo Streamlit
dashboard:
	@echo "Iniciando painel Streamlit..."
	python -m streamlit run src/dashboard.py --server.port 8501

# Exporta a especificação completa de documentação da API em JSON
docs:
	@echo "Gerando documentação OpenAPI do projeto..."
	python src/export_openapi.py

# Consulta os motores de hipóteses estatísticas direto da API ativa via script python nativo (cross-platform)
stats:
	@echo "Consultando resultados estatísticos reais (Spearman & Kruskal-Wallis)..."
	python -c "import requests, json; r=requests.get('http://127.0.0.1:8000/api/v1/analise/estatisticas'); print(json.dumps(r.json(), indent=2, ensure_ascii=False))"

# Limpeza e remoção de artefatos locais
clean:
	@echo "Limpando artefatos locais..."
	@if exist compras_governanca.db (del compras_governanca.db && echo Banco SQLite removido.) else (echo Banco SQLite não encontrado.)
	@if exist api_docs.json (del api_docs.json && echo Documentação api_docs.json removida.) else (echo api_docs.json não encontrado.)
