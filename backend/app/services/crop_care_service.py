import os
import logging
from typing import Dict

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough, RunnableSequence
from langchain_core.documents import Document
from langchain_community.retrievers import WikipediaRetriever, TavilySearchAPIRetriever
from langchain_community.utilities import SerpAPIWrapper

logger = logging.getLogger(__name__)


class CropCareRAGService:
    def __init__(self) -> None:
        try:
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-8b-8192"
            )
            logger.info("✅ Groq LLM initialized for Crop Care")
        except Exception as e:
            logger.error(f"❌ Groq initialization failed: {e}")
            raise

        # Initialize retrievers
        try:
            self.wiki_retriever = WikipediaRetriever()
            self.tavily_retriever = TavilySearchAPIRetriever(api_key=os.getenv("TAVILY_API_KEY"))
            self.serpapi_retriever = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))
            logger.info("✅ Crop care retrievers initialized")
        except Exception as e:
            logger.error(f"❌ Retriever initialization failed: {e}")
            raise

        # Prompt for agricultural expert
        self.crop_care_prompt = PromptTemplate.from_template("""
            You are a highly experienced agricultural expert and advisor.

            Your job is to help Indian farmers with accurate, practical, and understandable information related to all aspects of farming, including:

            - Crop growth and care
            - Disease identification and treatment
            - Farm machinery and tools
            - Organic and sustainable practices
            - Advanced technologies in agriculture
            - Fertilizer and pesticide usage
            - Post-harvest handling and storage
            - Weather impact on agriculture

            Use the context provided below (if any) to answer the farmer's question clearly and helpfully. If the context is not enough, answer based on your deep domain knowledge.

            ---------------------
            Context:
            {context}
            ---------------------

            Question:
            {question}

            Give your answer in a clear, farmer-friendly tone in English:
        """)

        # Build full chain
        self.rag_chain = self.build_rag_chain()

    def build_rag_chain(self) -> RunnableSequence:
        wiki_runnable = RunnableLambda(lambda x: self.wiki_retriever.invoke(x["question"]))
        tavily_runnable = RunnableLambda(lambda x: self.tavily_retriever.invoke(x["question"]))
        serpapi_runnable = RunnableLambda(lambda x: self.serpapi_retriever.run(x["question"]))

        retriever_chain = RunnableParallel({
            "wiki_docs": wiki_runnable,
            "tavily_docs": tavily_runnable,
            "serpapi_result": serpapi_runnable,
            "question": RunnablePassthrough()
        })

        formatter = RunnableLambda(self.format_docs)

        return (
            {"question": RunnablePassthrough()}
            | retriever_chain
            | formatter
            | self.crop_care_prompt
            | self.llm
        )

    @staticmethod
    def format_docs(inputs: Dict) -> Dict:
        all_docs = inputs["wiki_docs"] + inputs["tavily_docs"]
        context = "\n\n".join([doc.page_content for doc in all_docs])
        context += f"\n\nSerpAPI Search Result:\n{inputs['serpapi_result']}"
        return {"context": context, "question": inputs["question"]}

    def run_crop_care_pipeline(self, user_query: str) -> str:
        logger.info("🌱 Running Crop Care RAG pipeline")
        try:
            response = self.rag_chain.invoke(user_query)
            return response.content.strip()
        except Exception as e:
            logger.error(f"❌ Crop Care pipeline failed: {e}")
            return "Sorry, something went wrong while fetching crop care information."
