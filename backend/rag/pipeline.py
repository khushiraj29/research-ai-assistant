"""RAG (Retrieval-Augmented Generation) pipeline combining FAISS retrieval
with OpenAI language model responses via LangChain."""

import logging
from typing import Dict, List

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from backend.embeddings.generator import EmbeddingGenerator
from backend.rag.retriever import FAISSRetriever
from backend.utils.config import settings

logger = logging.getLogger(__name__)

# Prompt template used for the LLM call.
# The {context} block provides grounding; {question} is the user query.
_RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a helpful research assistant. Use the following context excerpts "
        "to answer the question accurately and concisely.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer (cite the source filenames where relevant):"
    ),
)


class RAGPipeline:
    """End-to-end retrieval-augmented generation pipeline.

    Workflow for each :meth:`query` call:
    1. Encode the user question into an embedding vector.
    2. Retrieve the top-k most similar document chunks from FAISS.
    3. Assemble a context string from the retrieved chunks.
    4. Call the OpenAI LLM via LangChain with the prompt + context.
    5. Return the answer together with source attribution metadata.

    Attributes:
        embedding_generator: Handles text → vector conversion.
        retriever: FAISS-backed chunk store and searcher.
        llm: LangChain ChatOpenAI model wrapper.
    """

    def __init__(self) -> None:
        """Initialise the embedding generator, FAISS retriever, and LLM."""
        self.embedding_generator = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL)
        self.retriever = FAISSRetriever(index_path=settings.FAISS_INDEX_PATH)
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.2,  # Lower temperature for factual research answers
        )
        logger.info("RAGPipeline initialised with model '%s'.", settings.LLM_MODEL)

    def query(self, question: str, top_k: int = 5) -> Dict:
        """Answer *question* using retrieved context from the document store.

        Args:
            question: Natural-language research question from the user.
            top_k: Number of document chunks to retrieve as context.

        Returns:
            A dict with keys:
                - ``answer``: The generated answer string.
                - ``sources``: List of source dicts, each with
                  ``document_id``, ``source_filename``, ``chunk_index``, and
                  ``score``.
                - ``model_used``: The LLM model identifier.
        """
        logger.info("RAG query: '%s' (top_k=%d)", question, top_k)

        # Step 1 – embed the question
        query_embedding = self.embedding_generator.generate_embedding(question)

        # Step 2 – retrieve relevant chunks
        retrieved_chunks = self.retriever.search(query_embedding, top_k=top_k)

        if not retrieved_chunks:
            return {
                "answer": (
                    "I don't have enough information in the document store to "
                    "answer this question. Please upload and process relevant "
                    "documents first."
                ),
                "sources": [],
                "model_used": settings.LLM_MODEL,
            }

        # Step 3 – build context string from retrieved chunks
        context_parts: List[str] = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_parts.append(
                f"[Source {i}: {chunk.get('source_filename', 'unknown')}]\n{chunk['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Step 4 – invoke the LLM with the assembled prompt
        prompt_value = _RAG_PROMPT.format(context=context, question=question)
        response = self.llm.invoke(prompt_value)
        answer: str = response.content if hasattr(response, "content") else str(response)

        # Step 5 – build source attribution list
        sources = [
            {
                "document_id": chunk.get("document_id", ""),
                "source_filename": chunk.get("source_filename", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "score": chunk.get("score", 0.0),
            }
            for chunk in retrieved_chunks
        ]

        logger.info("RAG answer generated; %d sources cited.", len(sources))
        return {
            "answer": answer,
            "sources": sources,
            "model_used": settings.LLM_MODEL,
        }
