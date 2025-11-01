# backend/tools/rag_tool.py

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from loguru import logger
from huggingface_hub import InferenceClient
import os


class RAGTool:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2",
                 chunks_path="E:\\assi\\backend\\data\\chunks\\nephrology_chunks.json",
                 index_path="E:\\assi\\backend\\data\\embeddings\\faiss_index.bin"):
        self.model_name = model_name
        self.chunks_path = chunks_path
        self.index_path = index_path

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.chunks = self._load_chunks()
        self.index, self.embeddings = self._build_or_load_index()

        # Initialize Hugging Face client
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            logger.warning("⚠️ HF_TOKEN not set. LLM generation will fail if used.")
        self.client = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            token=hf_token
        )

    # ------------------------------- #
    def _load_chunks(self):
        logger.info(f"Loading chunks from {self.chunks_path}")
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------- #
    def _build_or_load_index(self):
        """Load FAISS index if exists; else create and save"""
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)

        if Path(self.index_path).exists():
            logger.info("Loading existing FAISS index...")
            index = faiss.read_index(self.index_path)
            embeddings = np.load(self.index_path.replace(".bin", ".npy"))
            return index, embeddings

        logger.info("Creating new FAISS index...")
        embeddings = self.model.encode(self.chunks, show_progress_bar=True, convert_to_numpy=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        faiss.write_index(index, self.index_path)
        np.save(self.index_path.replace(".bin", ".npy"), embeddings)
        logger.success(f"✅ FAISS index created with {len(self.chunks)} chunks")
        return index, embeddings

    # ------------------------------- #
    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve top-k relevant chunks for a query"""
        query_emb = self.model.encode([query], convert_to_numpy=True)
        D, I = self.index.search(query_emb, top_k)
        results = [{"score": float(D[0][i]), "text": self.chunks[I[0][i]]} for i in range(top_k)]
        return results

    # ------------------------------- #
    def generate_answer(self, query: str, top_k: int = 3):
        """
        Full RAG process: retrieve, build context, and call Mistral LLM.
        """
        logger.info(f"🔍 Performing retrieval for query: {query}")
        retrieved = self.retrieve(query, top_k)
        context = "\n\n".join([r["text"] for r in retrieved])

        prompt = f"""
        You are a medical assistant helping with nephrology-related post-discharge care.
        Based on the context below, answer the user's question accurately and safely.

        Context:
        {context}

        Question:
        {query}

        Provide a short and safe answer.
        """

        try:
            logger.info("Sending prompt to Mistral LLM...")
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )
            answer = completion.choices[0].message["content"]
            logger.success("✅ Response generated successfully")

            return {
                "context": context,
                "answer": answer
            }

        except Exception as e:
            logger.error(f"❌ RAG generation error: {e}")
            return {
                "context": context,
                "answer": "Sorry, I encountered an issue generating the medical response."
            }


# ------------------------------- #
if __name__ == "__main__":
    rag = RAGTool()
    query = "What are the management guidelines for CKD?"
    result = rag.generate_answer(query)
    print("\n🩺 Answer:\n", result["answer"])
