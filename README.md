# Governança de TI e Análise Concorrencial de Fábricas de Software

Este projeto tem como finalidade realizar um **estudo analítico concorrencial** sobre as contratações de Fábrica de Software e Manutenção Evolutiva pela Administração Pública Federal, cobrindo o recorte temporal pós-sancionamento da Nova Lei de Licitações (Lei 14.133/2021).

---

## 🎯 Finalidade do Projeto

1. **Mensuração de Concentração de Mercado**:
   * Cálculo dos índices **HHI (Herfindahl-Hirschman Index)** e **CR4 (Concentration Ratio)** para classificar o nível de competitividade das contratações de TI por tecnologia (Java, .NET, PHP, Mobile, Mainframe, etc.) e ano (2024–2026).
2. **Avaliação da Governança de TI (COBIT)**:
   * Mapeamento direto entre a concentração econômica medida e os riscos de dependência de fornecedores (vendor lock-in), avaliando o alinhamento com as práticas **APO10 (Gerenciar Fornecedores)** e **APO12 (Gerenciar Riscos)** do COBIT.
3. **Modelagem Estatística**:
   * Validação científica através de testes de correlação não-paramétrica (Spearman) e testes de hipóteses de distribuição (Kruskal-Wallis) para garantir o rigor acadêmico do estudo.

---

## 📂 Estrutura do Repositório

* `compras_governanca.db`: Banco de dados SQLite com dados consolidados de órgãos, contratos, itens de licitação e fornecedores ativos.
* `src/dashboard.py`: Aplicação Streamlit contendo a interface visual rica do dashboard e gráficos dinâmicos/interativos (Plotly Express).
* `Makefile`: Atalhos para automação de tarefas de instalação e inicialização.

---

## 🚀 Como Executar

### 1. Instalar as Dependências
Prepare o ambiente virtual Python e instale os pacotes requeridos:
```bash
make install
```

### 2. Inicializar o Dashboard
Rode a interface interativa no seu navegador local:
```bash
make dashboard
```
O Streamlit abrirá automaticamente no endereço: [http://localhost:8501](http://localhost:8501).
