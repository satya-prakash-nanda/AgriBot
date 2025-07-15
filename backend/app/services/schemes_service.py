import os
import logging
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.retrievers import WikipediaRetriever
from duckduckgo_search import DDGS

from app.services.retriever import SchemeRetriever  # Pinecone retriever

logger = logging.getLogger(__name__)


# Simple DuckDuckGo retriever
class SimpleDuckDuckGoRetriever:
    def __init__(self, k: int = 3):
        self.k = k

    def invoke(self, query: str) -> List[Document]:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=self.k)
            return [
                Document(page_content=r.get("body", ""), metadata={"source": r.get("href", "")})
                for r in results if "body" in r and "href" in r
            ]


# Full Schemes RAG Service
class SchemesRAGService:
    def __init__(self) -> None:
        try:
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-8b-8192"
            )
            logger.info("✅ Groq LLM initialized for RAG")
        except Exception as e:
            logger.error(f"❌ Groq initialization failed: {e}")
            raise

        try:
            self.scheme_retriever = SchemeRetriever()  # Pinecone retriever
            self.wikipedia_retriever = WikipediaRetriever(top_k_results=3, lang="en")
            self.duckduckgo_retriever = SimpleDuckDuckGoRetriever(k=3)
            logger.info("✅ All retrievers initialized")
        except Exception as e:
            logger.error(f"❌ Retriever initialization failed: {e}")
            raise

        # Prompt templates
        self.rewrite_prompt = PromptTemplate.from_template(
            "Rewrite the following user query to optimize it for document retrieval.\n"
            "Only return the rewritten query itself, no explanation.\n\n"
            "User Query: {question}\nRewritten Query:"
        )

        self.compression_prompt = PromptTemplate.from_template(
            "Summarize the following document by keeping only the parts relevant to answering the user's question.\n\n"
            "User Question: {question}\n\nDocument:\n{document}\n\nCompressed Content:"
        )

        self.final_prompt = PromptTemplate.from_template(
            "You are an expert assistant for Indian farmers. Use the following context to answer the user's question.\n\n"
            "Context:\n{context}\n\nUser Question: {question}\n\nAnswer:"
        )

    # 1. Rewrite the input query for better retrieval
    def rewrite_query(self, query: str) -> str:
        response = self.llm.invoke(self.rewrite_prompt.format(question=query))
        return response.content.strip()

    # 2. Retrieve documents from all retrievers
    def retrieve_documents(self, query: str) -> List[Document]:
        all_docs = []

        try:
            pinecone_docs = self.scheme_retriever.retrieve(query)
            logger.info(f"🔍 Retrieved {len(pinecone_docs)} docs from Pinecone")
            all_docs.extend(pinecone_docs)
        except Exception as e:
            logger.error(f"❌ Pinecone retrieval failed: {e}")

        try:
            wiki_docs = self.wikipedia_retriever.invoke(query)
            logger.info(f"🔍 Retrieved {len(wiki_docs)} docs from Wikipedia")
            all_docs.extend(wiki_docs)
        except Exception as e:
            logger.error(f"❌ Wikipedia retrieval failed: {e}")

        try:
            ddg_docs = self.duckduckgo_retriever.invoke(query)
            logger.info(f"🔍 Retrieved {len(ddg_docs)} docs from DuckDuckGo")
            all_docs.extend(ddg_docs)
        except Exception as e:
            logger.error(f"❌ DuckDuckGo retrieval failed: {e}")

        return all_docs

    # 3. Compress each document to save tokens
    def compress_documents(self, docs: List[Document], query: str) -> List[Document]:
        compressed = []
        for doc in docs:
            try:
                response = self.llm.invoke(self.compression_prompt.format(question=query, document=doc.page_content))
                compressed.append(Document(page_content=response.content.strip(), metadata=doc.metadata))
            except Exception as e:
                logger.error(f"❌ Compression failed for a document: {e}")
        return compressed

    # 4. Generate the final answer from context
    def generate_answer(self, context_docs: List[Document], query: str) -> str:
        context = "\n\n".join(doc.page_content for doc in context_docs[:5])  # limit to 5 chunks
        try:
            response = self.llm.invoke(self.final_prompt.format(context=context, question=query))
            return response.content.strip()
        except Exception as e:
            logger.error(f"❌ Answer generation failed: {e}")
            return "Sorry, I couldn't generate an answer."

    # 5. Complete RAG pipeline
    def run_rag_pipeline(self, user_query: str) -> str:
        logger.info("🚀 Running RAG pipeline")
        try:
            # Rewrite query to improve retrieval
            rewritten_query = self.rewrite_query(user_query)
            logger.info(f"🔧 Rewritten query: {rewritten_query}")

            # Retrieve from all retrievers
            docs = self.retrieve_documents(rewritten_query)

            if not docs:
                return "Sorry, I couldn't find relevant government schemes or information."

            # Compress documents to save tokens
            compressed_docs = self.compress_documents(docs, rewritten_query)

            # Generate answer
            final_answer = self.generate_answer(compressed_docs, user_query)
            return final_answer

        except Exception as e:
            logger.error(f"❌ RAG pipeline failed: {e}")
            return "Sorry, something went wrong while retrieving schemes."
