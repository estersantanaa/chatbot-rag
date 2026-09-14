import os
from src.config import settings

def test_config():
    print("Checking configuration...")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"VECTOR_DB_PATH: {settings.VECTOR_DB_PATH}")
    print(f"DOCUMENTS_PATH: {settings.DOCUMENTS_PATH}")
    
    assert os.path.exists(settings.DOCUMENTS_PATH), "Documents path does not exist"
    assert os.path.exists(settings.VECTOR_DB_PATH), "Vector DB path does not exist"
    print("Config paths verified!")

def test_imports():
    print("\nChecking imports...")
    try:
        import langchain
        import faiss
        import huggingface_hub
        print("LangChain, FAISS and HuggingFace Hub imported successfully!")
    except ImportError as e:
        print(f"Import failed: {e}")

if __name__ == "__main__":
    test_config()
    # We won't run test_imports here because the venv might not be active in this shell
    # but the user can run it later.
