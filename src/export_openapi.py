import json
import sys
import os

# Adiciona o diretório atual ao sys.path para garantir importações corretas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api import app
except ModuleNotFoundError:
    from src.api import app

from fastapi.openapi.utils import get_openapi

def exportar_docs():
    print("Gerando documentação OpenAPI do FastAPI...")
    
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_docs.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        
    print(f"Documentação exportada com sucesso em: {file_path}")

if __name__ == "__main__":
    exportar_docs()
