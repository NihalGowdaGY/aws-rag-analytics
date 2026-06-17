import os

class AppSettings:
    def __init__(self):
        # Sys runtime auth
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

        self.chunk_size = 1000      
        self.chunk_overlap = 200     
        self.top_k_retrieval = 3     

        # Infra Model Targets
        self.embedding_model = "all-MiniLM-L6-v2" 
        self.llm_model = "gemini-2.5-flash"        

        # Data & DB Storage Path Mapping
        self.database_url = "sqlite:///./query_analytics.db"
        self.source_pdf_path = "data/AWS Customer Agreement.pdf"

settings = AppSettings()