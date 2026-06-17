import os
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types
from src.config import settings

class LegalRAGProcessor:
    def __init__(self):
        self.encoder = SentenceTransformer(settings.embedding_model)
        
        if not settings.gemini_api_key:
            raise ValueError("Environment variable GEMINI_API_KEY is not initialized.")
            
        self.ai_client = genai.Client(api_key=settings.gemini_api_key)
        self.segments = []
        self.vector_index = None

    def load_and_segment_document(self) -> list[str]:
        """Loads target contract PDF and splits string contents using rolling index windows."""
        if not os.path.exists(settings.source_pdf_path):
            raise FileNotFoundError(f"Target document path missing: {settings.source_pdf_path}")
            
        reader = PdfReader(settings.source_pdf_path)
        extracted_text_buffer = []
        
        for page in reader.pages:
            page_content = page.extract_text()
            if page_content:
                extracted_text_buffer.append(page_content)
                
        compiled_corpus = "\n".join(extracted_text_buffer).strip()
        
        if not compiled_corpus:
            print(f"WARNING: File located at '{settings.source_pdf_path}' contains empty or unreadable string data.")
            self.segments = []
            return []
        
        segments = []
        pointer = 0
        corpus_length = len(compiled_corpus)
        
        while pointer < corpus_length:
            end_pointer = pointer + settings.chunk_size
            text_slice = compiled_corpus[pointer:end_pointer].strip()
            if text_slice:
                segments.append(text_slice)
            pointer += (settings.chunk_size - settings.chunk_overlap)
            
        self.segments = segments
        return segments

    def generate_vector_index(self) -> bool:
        """Generates localized mathematical vector representations using Euclidean Flat L2 indices."""
        if not self.segments:
            self.load_and_segment_document()
            
        # Halts processing cleanly if the segment collection remains entirely empty
        if not self.segments:
            return False
            
        raw_embeddings = self.encoder.encode(self.segments, show_progress_bar=False)
        matrix_array = np.array(raw_embeddings).astype("float32")
        
        dimensions = matrix_array.shape[1]
        self.vector_index = faiss.IndexFlatL2(dimensions)
        self.vector_index.add(matrix_array)
        return True

    def execute_retrieval_query(self, query_text: str) -> tuple[list[str], str]:
        """Retrieves top matches, flags contexts, and returns deterministic answers from the LLM."""
        if self.vector_index is None:
            initialization_successful = self.generate_vector_index()
            if not initialization_successful:
                return [], "System engine failed to execute: Source data segment index mapping is empty."
            
        query_vector = np.array([self.encoder.encode(query_text)]).astype("float32")
        _, structural_indices = self.vector_index.search(query_vector, settings.top_k_retrieval)
        
        matched_contexts = []
        for index_pos in structural_indices[0]:
            if index_pos != -1 and index_pos < len(self.segments):
                matched_contexts.append(self.segments[index_pos])
                
        if not matched_contexts:
            return [], "I am sorry, but the provided documentation does not contain that information."
            
        context_payload = "\n---\n".join(matched_contexts)
        
        system_guardrails = (
            "You are a strict technical contract inspector reviewing the attached AWS Customer Agreement.\n"
            "Analyze the Context Material below to provide your determination.\n\n"
            "OPERATIONAL INSTRUCTIONS:\n"
            "1. Rely ONLY on explicit assertions found inside the Context Material block.\n"
            "2. If the answer cannot be confidently derived from the provided context, you must output exactly:\n"
            "   'I am sorry, but the provided documentation does not contain that information.'\n"
            "3. Do not construct external assumptions, extrapolation, or general knowledge statements."
        )
        
        prompt_feed = f"Context Material:\n{context_payload}\n\nUser Inquiry: {query_text}"
        
        try:
            execution_response = self.ai_client.models.generate_content(
                model=settings.llm_model,
                contents=prompt_feed,
                config=types.GenerateContentConfig(
                    system_instruction=system_guardrails,
                    temperature=0.0
                )
            )
            return matched_contexts, execution_response.text
        except Exception as error:
            return matched_contexts, f"System Engine Processing Fault: {str(error)}"

rag_backend = LegalRAGProcessor()