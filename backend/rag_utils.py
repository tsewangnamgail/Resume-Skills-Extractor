"""
rag_utils.py - RAG retrieval and Groq embedding utilities
"""

import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions

from config import settings


class TextChunker:
    """Utility class for splitting text into chunks."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (roughly 4 characters per token)."""
        return len(text) // 4
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks of approximately chunk_size tokens."""
        # Clean the text
        text = self._clean_text(text)
        
        # Split into sentences first for better chunking
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            
            if current_size + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Keep overlap
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    s_tokens = self.estimate_tokens(s)
                    if overlap_size + s_tokens <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,;:!?@#$%&*()\-+=/\'"]+', '', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class GroqClient:
    """Client for Groq API interactions."""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> str:
        """Generate a completion using Groq LLM."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Groq.
        Note: Groq doesn't have a native embedding endpoint, 
        so we use a workaround with the LLM or fall back to 
        a simple embedding function.
        """
        # Using a hash-based embedding as fallback
        # In production, use a proper embedding model like sentence-transformers
        embeddings = []
        for text in texts:
            # Create a deterministic embedding based on text content
            embedding = self._create_simple_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _create_simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Create a simple deterministic embedding (for demo purposes)."""
        # Hash the text to create consistent embeddings
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Convert hash to embedding vector
        embedding = []
        for i in range(0, min(len(text_hash), dim * 2), 2):
            val = int(text_hash[i:i+2], 16) / 255.0 - 0.5
            embedding.append(val)
        
        # Pad or truncate to desired dimension
        while len(embedding) < dim:
            embedding.append(0.0)
        
        return embedding[:dim]


class ChromaVectorStore:
    """Wrapper for ChromaDB operations."""
    
    def __init__(self):
        # Use PersistentClient instead of deprecated Settings pattern
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Use default embedding function or custom one
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self._collections: Dict[str, Any] = {}
    
    def get_or_create_collection(self, collection_name: str) -> Any:
        """Get or create a Chroma collection."""
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        return self._collections[collection_name]
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to a collection."""
        collection = self.get_or_create_collection(collection_name)
        
        # Add in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
    
    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query a collection for similar documents."""
        collection = self.get_or_create_collection(collection_name)
        
        query_params = {
            "query_texts": query_texts,
            "n_results": n_results
        }
        
        if where_filter:
            query_params["where"] = where_filter
        
        return collection.query(**query_params)
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
        except Exception:
            pass
    
    def get_all_documents(
        self,
        collection_name: str,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get all documents from a collection."""
        collection = self.get_or_create_collection(collection_name)
        
        get_params = {}
        if where_filter:
            get_params["where"] = where_filter
        
        return collection.get(**get_params)


class RAGProcessor:
    """Main RAG processing class."""
    
    def __init__(self):
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        self.groq_client = GroqClient()
        self.vector_store = ChromaVectorStore()
    
    def index_resume(
        self,
        job_id: str,
        candidate_id: str,
        candidate_name: str,
        resume_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Index a resume into the vector store."""
        # Chunk the resume
        chunks = self.chunker.chunk_text(resume_text)
        
        if not chunks:
            return 0
        
        # Prepare documents for indexing
        documents = []
        metadatas = []
        ids = []
        
        base_metadata = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            **(metadata or {})
        }
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{job_id}_{candidate_id}_chunk_{i}"
            chunk_metadata = {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            documents.append(chunk)
            metadatas.append(chunk_metadata)
            ids.append(chunk_id)
        
        # Add to vector store
        collection_name = f"job_{job_id}_resumes"
        self.vector_store.add_documents(
            collection_name=collection_name,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(chunks)
    
    def retrieve_relevant_chunks(
        self,
        job_id: str,
        query: str,
        candidate_id: Optional[str] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query."""
        top_k = top_k or settings.TOP_K_CHUNKS
        collection_name = f"job_{job_id}_resumes"
        
        where_filter = None
        if candidate_id:
            where_filter = {"candidate_id": candidate_id}
        
        results = self.vector_store.query(
            collection_name=collection_name,
            query_texts=[query],
            n_results=top_k,
            where_filter=where_filter
        )
        
        # Format results
        retrieved_chunks = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                chunk_data = {
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                }
                retrieved_chunks.append(chunk_data)
        
        return retrieved_chunks
    
    def get_candidate_context(
        self,
        job_id: str,
        candidate_id: str,
        jd_text: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Get all relevant context for a candidate based on JD."""
        # Retrieve chunks relevant to the JD
        relevant_chunks = self.retrieve_relevant_chunks(
            job_id=job_id,
            query=jd_text,
            candidate_id=candidate_id,
            top_k=settings.TOP_K_CHUNKS * 2  # Get more chunks for comprehensive evaluation
        )
        
        # Combine chunks into context
        context_parts = []
        for chunk in relevant_chunks:
            context_parts.append(chunk["content"])
        
        full_context = "\n\n".join(context_parts)
        
        return full_context, relevant_chunks
    
    def get_all_candidates_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all unique candidates for a job."""
        collection_name = f"job_{job_id}_resumes"
        
        try:
            all_docs = self.vector_store.get_all_documents(collection_name)
            
            # Extract unique candidates
            candidates = {}
            if all_docs and all_docs.get("metadatas"):
                for metadata in all_docs["metadatas"]:
                    cid = metadata.get("candidate_id")
                    if cid and cid not in candidates:
                        candidates[cid] = {
                            "candidate_id": cid,
                            "candidate_name": metadata.get("candidate_name", "Unknown"),
                            "metadata": {k: v for k, v in metadata.items() 
                                       if k not in ["candidate_id", "candidate_name", "chunk_index", "total_chunks"]}
                        }
            
            return list(candidates.values())
        except Exception:
            return []
    
    def evaluate_with_llm(
        self,
        jd_text: str,
        candidate_context: str,
        candidate_name: str,
        mandatory_skills: List[str],
        optional_skills: List[str]
    ) -> Dict[str, Any]:
        """Use Groq LLM to evaluate a candidate against JD."""
        
        system_prompt = """You are an AI-powered ATS evaluation engine. Evaluate the candidate strictly based on the provided resume content and job description.

RULES:
- Use ONLY the provided information
- Do NOT hallucinate or assume missing details
- Normalize skill synonyms (e.g., JS → JavaScript)
- Penalize missing mandatory skills heavily
- Be objective and unbiased
- Return ONLY valid JSON"""

        evaluation_prompt = f"""
Evaluate this candidate against the job description.

JOB DESCRIPTION:
{jd_text}

MANDATORY SKILLS: {json.dumps(mandatory_skills)}
OPTIONAL SKILLS: {json.dumps(optional_skills)}

CANDIDATE RESUME CONTENT:
{candidate_context}

Provide evaluation in this EXACT JSON format:
{{
    "matched_skills": ["list of skills found in resume that match JD"],
    "missing_skills": ["list of required skills NOT found in resume"],
    "skills_score": <0-100 number>,
    "experience_summary": "brief summary of relevant experience",
    "experience_score": <0-100 number>,
    "education_details": "education and certifications found",
    "education_score": <0-100 number>,
    "strengths": ["list of 2-4 key strengths"],
    "weaknesses": ["list of 1-3 weaknesses or gaps"],
    "confidence_notes": "brief justification based on resume evidence"
}}

Return ONLY the JSON object, no other text."""

        try:
            response = self.groq_client.generate_completion(
                prompt=evaluation_prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            # Parse JSON from response
            # Clean potential markdown formatting
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```json?\n?', '', response)
                response = re.sub(r'\n?```$', '', response)
            
            evaluation = json.loads(response)
            return evaluation
            
        except json.JSONDecodeError as e:
            # Return conservative scores on parse error
            return {
                "matched_skills": [],
                "missing_skills": mandatory_skills,
                "skills_score": 0,
                "experience_summary": "Unable to parse resume content",
                "experience_score": 0,
                "education_details": "Unknown",
                "education_score": 0,
                "strengths": [],
                "weaknesses": ["Resume parsing failed"],
                "confidence_notes": f"Evaluation failed due to parsing error: {str(e)}"
            }
        except Exception as e:
            return {
                "matched_skills": [],
                "missing_skills": mandatory_skills,
                "skills_score": 0,
                "experience_summary": "Evaluation error",
                "experience_score": 0,
                "education_details": "Unknown",
                "education_score": 0,
                "strengths": [],
                "weaknesses": ["Evaluation failed"],
                "confidence_notes": f"LLM evaluation failed: {str(e)}"
            }