# Estrutura Modular do Artigo Científico

Este diretório contém a estrutura modular para a redação do artigo científico que investiga a governança de TI e a concentração de mercado em contratações de Fábrica de Software no governo federal sob a Nova Lei de Licitações (Lei 14.133/2021) no período de 2024-2026.

A estrutura foi projetada para simular o comportamento de sistemas modulares de escrita científica (como o Overleaf/LaTeX), onde o conteúdo do artigo é subdividido em módulos lógicos em arquivos independentes e acoplado através de um documento mestre.

## Estrutura do Diretório

- `main.md`: Arquivo mestre que centraliza e apresenta a estrutura lógica do artigo completo.
- `referencias.md`: Relação centralizada de referências bibliográficas do artigo, em estrita conformidade com a ABNT NBR 6023.
- `secoes/`: Diretório contendo os arquivos individuais de cada capítulo ou seção do artigo:
  - `0_resumo.md`: Resumo (Abstract) e palavras-chave.
  - `1_introducao.md`: Introdução, problematização e objetivos da pesquisa.
  - `2_referencial.md`: Revisão da literatura (Governança de TI, COBIT 5, Concentração de Mercado, HHI, Gini, CR4).
  - `3_metodologia.md`: Detalhamento do Procedimento Metodológico (coleta de dados, métricas e análises estatísticas).
  - `4_resultados.md`: Apresentação das métricas quantitativas e discussões teórico-práticas.
  - `5_conclusao.md`: Considerações finais, limitações e sugestões para trabalhos futuros.

## Diretrizes para Edição e Escrita

Para manter a integridade acadêmica do manuscrito, todas as contribuições e edições devem observar as seguintes regras:
1. **Impessoalidade**: A escrita deve ser realizada em terceira pessoa do singular ou utilizando voz passiva (ex: "observa-se", "analisou-se").
2. **Linguagem de Mitigação (Hedging)**: Evitar afirmações dogmáticas ou definitivas sobre correlações ou efeitos. Os dados coletados apontam correlações e tendências na amostra delimitada, não verdades absolutas. Prefira expressões como "os resultados sugerem que", "há indícios de uma tendência", "pode-se inferir que".
3. **Citações**: Seguir estritamente o padrão autor-data definido pela ABNT NBR 10520 (ex: `(SILVA, 2023)` para citação ao final do período, ou `Segundo Silva (2023)` integrado ao fluxo do texto).
4. **Referências**: Toda obra citada no corpo do texto deve obrigatoriamente constar no arquivo `referencias.md`.
