import os

class Settings:
    # 1. API Credentials
    # Dynamically reads your Gemini API token from your active terminal environment variables
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # 2. RAG Hyperparameters (Directly addresses the assignment requirements)
    CHUNK_SIZE: int = 1000       # Slices layout text into readable paragraph blocks [cite: 458]
    CHUNK_OVERLAP: int = 200     # Preserves vocabulary/semantic flow across sequential splits [cite: 458]
    RETRIEVAL_K: int = 3         # Fetches the top 3 highest matching data chunks [cite: 461]
    
    # 3. Model Profiles
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"  # Free local mathematical encoding framework [cite: 459]
    LLM_MODEL_NAME: str = "gemini-2.5-flash"        # Stable generation engine model profile [cite: 461]
    
    # 4. Storage Locations
    DATABASE_URL: str = "sqlite:///./query_analytics.db"  # Dedicated SQLite storage path [cite: 465]
    PDF_PATH: str = "data/AWS Customer Agreement.pdf"     # Core data source location [cite: 454]

settings = Settings()