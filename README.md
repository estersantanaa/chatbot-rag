# Chatbot RAG

Repositório para o projeto de Chatbot com RAG (Retrieval-Augmented Generation).

## Estrutura do Projeto:
- `src/`: Código fonte principal.
- `data/`: Documentos para o RAG (PDFs, TXTs, etc).
- `vector_db/`: Banco de dados vetorial local (ChromaDB).
- `venv/`: Ambiente virtual Python.
- `.env`: Variáveis de ambiente (use `.env.example` como base).

## Como configurar:
1.  **Venv**: O ambiente virtual já foi criado. Ative-o com:
    ```powershell
    .\venv\Scripts\activate
    ```
2.  **Dependências**: Instaladas via `requirements.txt`.
3.  **Configuração**: Renomeie `.env.example` para `.env` e adicione sua `GROQ_API_KEY`.

## Testes:
- `test_ai_core.py`: Testes do núcleo de IA.
- `test_db.py`: Testes de banco de dados.
- `test_groq.py`: Testes da API Groq.
- `test_rag_setup.py`: Validação da infraestrutura de RAG.
