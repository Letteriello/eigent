# Memória do Backend Developer

## Padrões do Projeto

- Backend em backend/app/
- Controllers em backend/app/controller/
- Services em backend/app/service/
- Models em backend/app/model/
- Toolkits em backend/app/agent/toolkit/

## Tecnologias

- Python 3.11
- FastAPI
- Pydantic
- uv para gerenciamento de pacotes
- pytest para testes

## Estrutura de Toolkits

- Herdar de AbstractToolkit
- Implementar get_tools() retornando FunctionTool list
- Run command: cd backend && uv run uvicorn main:app --reload

## Regras de Código

- Usar ruff check --fix antes de commitar
- Rodar pytest para testes
- Seguir padrões existentes de imports
