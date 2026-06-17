import os
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types
from src.config import settings

class LegalRAGProcessor:
    def __init__(self):
        """Initializes semantic encoders, index storage parameters, and core model clients."""
        self.encoder = SentenceTransformer(settings.embedding_model)
        self.client = genai.Client(api_key=settings.gemini_api_key)
        
        # Base data layers
        self.text_chunks = []
        self.index = None
        
        
        self.index_file = "index.faiss"
        self.chunks_file = "chunks.txt"
        
        
        self.load_persisted_index()

    def load_and_segment_document(self):
        """Parses target legal text inputs and extracts overlapping string windows."""
        if not os.path.exists(settings.source_pdf_path):
            raise FileNotFoundError(f"Missing source document asset at: {settings.source_pdf_path}")
            
        reader = PdfReader(settings.source_pdf_path)
        raw_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"
                
        self.text_chunks = []
        pointer = 0
        while pointer < len(raw_text):
            chunk = raw_text[pointer : pointer + settings.chunk_size]
            self.text_chunks.append(chunk)
            pointer += settings.chunk_size - settings.chunk_overlap

    def generate_vector_index(self):
        """Generates embeddings and writes the binary index maps out to disk storage files."""
        if not self.text_chunks:
            raise ValueError("No text fragments segmented to execute vector coordinate maps.")
            
        embeddings = self.encoder.encode(self.text_chunks, show_progress_bar=False)
        matrix = np.array(embeddings).astype("float32")
        
        dimension = matrix.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(matrix)
        
        
        faiss.write_index(self.index, self.index_file)
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            for chunk in self.text_chunks:
                f.write(chunk.replace("\n", " ") + "\n")

    def load_persisted_index(self):
        """Loads index files from storage to bypass redundant ingestion steps on startup."""
        if os.path.exists(self.index_file) and os.path.exists(self.chunks_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, "r", encoding="utf-8") as f:
                self.text_chunks = [line.strip() for line in f if line.strip()]

    def execute_retrieval_query(self, user_query: str) -> tuple[list[str], str]:
        """Queries nearest neighbors from the index and builds the grounded prompt matrix."""
        if self.index is None or not self.text_chunks:
            return [], "System vector index is offline. Please execute document ingestion first."
            
        query_vector = self.encoder.encode([user_query]).astype("float32")
        distances, indices = self.index.search(query_vector, settings.top_k_retrieval)
        
        matched_chunks = []
        for idx in indices[0]:
            if 0 <= idx < len(self.text_chunks):
                matched_chunks.append(self.text_chunks[idx])
                
        if not matched_chunks:
            return [], "I am sorry, but the provided documentation does not contain that information."
            
        context_block = "\n---\n".join(matched_chunks)
        system_rules = (
            "You are a precise corporate legal compliance auditor tracking contractual risk elements.\n"
            "Your sole objective is to answer user inquiries using only the explicit facts provided inside the Context Material.\n"
            "Guardrails:\n"
            "1. Rely ONLY on explicit assertions found inside the Context Material. Do not extrapolate or assume.\n"
            "2. If the Context Material does not directly answer the question, state exactly: "
            "'I am sorry, but the provided documentation does not contain that information.'\n"
            "3. Keep your assertions factual, clinical, and clear without editorial commentary."
        )
        
        response = self.client.models.generate_content(
            model=settings.llm_model,
            contents=f"Context Material:\n{context_block}\n\nUser Question: {user_query}",
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.0
            )
        )
        return matched_chunks, response.text