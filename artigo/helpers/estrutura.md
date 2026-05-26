1. Introdução
   1.1 Contextualização (a relevância crítica da Fábrica de Software no setor público)
   1.2 O ecossistema de contratações federais e o portal Compras.gov.br
   1.3 Problema de Pesquisa: A concentração de mercado em contratações de alta tecnologia
   1.4 Objetivos e relevância acadêmica/prática

2. Referencial Teórico
   2.1 Governança Corporativa e Pública de TI (COBIT 5)
   2.2 O Processo APO10 (Gestão de Fornecedores): Habilitadores, práticas e riscos de Lock-In
   2.3 O Processo APO12 (Gestão de Riscos): Risco de concentração e dependência sistêmica
   2.4 Concentração de Mercado (HHI) aplicada ao Setor Público (Public Procurement)
   2.5 O ecossistema de Fábrica de Software: Desenvolvimento vs. Manutenção Evolutiva

3. Procedimento Metodológico
   3.1 Coleta de dados via API de Dados Abertos do Compras.gov.br
   3.2 Filtro e extração estruturada (Utilização dos 14 códigos CATSER)
   3.3 Tratamento de dados e cálculo das proxies de mercado (Market Share dos Fornecedores)
   3.4 Modelagem Estatística:
       - Cálculo do HHI (Herfindahl-Hirschman Index) por CATSER e por ano
       - Cálculo do CR4 (Concentration Ratio dos 4 maiores fornecedores)
       - Testes de Correlação Não-Paramétrica (Spearman)
   3.5 Abordagem Teórico-Analítica: Mapeamento dos índices quantitativos para as práticas APO10 e APO12

4. Análise e Resultados
   4.1 Panorama geral das contratações de Fábrica de Software (2021-2026)
   4.2 Análise Comparativa de Concentração: Desenvolvimento vs. Manutenção Evolutiva
   4.3 Análise por Stack Tecnológica (Java vs. .NET vs. PHP vs. Linguagens Web/Mobile/Mainframe)
   4.4 Discussão COBIT: Como a concentração quantificada afeta as métricas APO10 e APO12 no Governo Federal

5. Considerações Finais
   5.1 Principais achados (quais stacks são críticas, onde há maior dependência)
   5.2 Implicações de política pública para governança de TI governamental
   5.3 Limitações metodológicas da API do Compras.gov.br
   5.4 Próximos passos de pesquisa