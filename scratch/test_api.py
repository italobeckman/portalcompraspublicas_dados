"""
test_api.py — Teste pontual do endpoint dadosabertos.compras.gov.br

ATENÇÃO: O parâmetro obrigatório é 'codigoltemCatalogo' com 'l' minúsculo.
Usar 'codigoItemCatalogo' com 'I' maiúsculo retorna 400 ou vazio.
"""
import requests
import json

url = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico"

# Testa o CATSER 25852 (Desenvolvimento Java)
params = {
    "pagina": 1,
    "codigoItemCatalogo": 25852,   # I maiúsculo — correto na API de produção
}

print(f"URL: {url}")
print(f"Params: {params}\n")

try:
    response = requests.get(url, params=params, timeout=15)
    print(f"Status Code : {response.status_code}")
    print(f"URL final   : {response.url}\n")

    if response.status_code == 200:
        data = response.json()
        total_regs  = data.get("totalRegistros", "?")
        total_pags  = data.get("totalPaginas", "?")
        pags_rest   = data.get("paginasRestantes", "?")
        resultados  = data.get("resultado", [])

        print(f"totalRegistros   : {total_regs}")
        print(f"totalPaginas     : {total_pags}")
        print(f"paginasRestantes : {pags_rest}")
        print(f"Itens nesta pág  : {len(resultados)}\n")

        if resultados:
            print("Primeiro item retornado:")
            print(json.dumps(resultados[0], indent=2, ensure_ascii=False))
    else:
        print("Resposta de erro:")
        print(response.text[:500])

except Exception as e:
    print(f"Erro ao conectar: {e}")
