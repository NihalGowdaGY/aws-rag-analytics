import os

class Settings:
    # 1. API Credentials
    # This reads the Gemini token directly from your active Windows terminal session
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # 2. RAG Hyperparameters (Per the assignment's criteria)
    CHUNK_SIZE: int = 1000       # Slices the text into clear paragraph blocks
    CHUNK_OVERLAP: int = 200     # Ensures sentence continuity between blocks
    RETRIEVAL_K: int = 3         # Fetches the top 3 highest matching blocks
    
    # 3. Database & File Locations
    DATABASE_URL: str = "sqlite:///./query_analytics.db"
    PDF_PATH: str = "data/AWS Customer Agreement.pdf"

settings = Settings()