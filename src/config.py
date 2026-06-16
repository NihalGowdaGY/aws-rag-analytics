import os

class AppSettings:
    def __init__(self):
        # System Runtime Authentication
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

        # RAG Pipeline Hyperparameters
        self.chunk_size = 1000       # Token window boundary for contractual sentences
        self.chunk_overlap = 200     # Buffer to retain paragraph context across cuts
        self.top_k_retrieval = 3     # Nearest-neighbor matching threshold count

        # Infrastructure Model Targets
        self.embedding_model = "all-MiniLM-L6-v2"  # Local text encoder mapping model
        self.llm_model = "gemini-2.5-flash"        # Generative routing core engine model

        # Data & Database Storage Path Mapping
        self.database_url = "sqlite:///./query_analytics.db"
        self.source_pdf_path = "data/AWS Customer Agreement.pdf"

settings = AppSettings()