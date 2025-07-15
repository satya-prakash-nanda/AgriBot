# backend/app/services/retriever.py

import os
import re
import logging
from typing import List

from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

logger = logging.getLogger(__name__)


class SchemeRetriever:
    def __init__(self, file_path: str = "rag_store/schemes.txt") -> None:
        self.file_path = file_path
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "schemes")
        self.embedding_model = HuggingFaceEmbeddings(model_name="intfloat/e5-large-v2")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")

        if not self.pinecone_api_key:
            raise ValueError("❌ Missing PINECONE_API_KEY")

        self._init_pinecone()
        self._load_or_create_index()

    def _init_pinecone(self):
        try:
            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            logger.info("✅ Pinecone client initialized")
        except Exception as e:
            logger.error(f"❌ Pinecone init error: {e}")
            raise

    def _load_or_create_index(self):
        if self.index_name not in self.pinecone_client.list_indexes().names():
            logger.info("📌 Creating new Pinecone index")
            self.pinecone_client.create_index(
                name=self.index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index = self.pinecone_client.Index(self.index_name)
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embedding_model
        )

    def load_and_upload_documents(self):
        logger.info("📂 Loading schemes from file")
        loader = TextLoader(self.file_path, encoding="utf-8")
        documents = loader.load()

        full_text = "\n".join(doc.page_content for doc in documents)
        raw_schemes = re.split(r"### Scheme:\s*", full_text)[1:]

        parsed_docs = []
        for scheme in raw_schemes:
            title = re.match(r"(.+?)\s*Type:", scheme).group(1).strip()
            type_match = re.search(r"Type:\s*(.+?)\s*Tags:", scheme)
            tags_match = re.search(r"Tags:\s*(.+?)\s*Description:", scheme)
            desc_match = re.search(r"Description:\s*(.+)", scheme, re.DOTALL)

            doc = Document(
                page_content=desc_match.group(1).strip() if desc_match else "",
                metadata={
                    "title": title,
                    "type": type_match.group(1).strip() if type_match else "",
                    "tags": [tag.strip() for tag in tags_match.group(1).split(",")] if tags_match else []
                }
            )
            parsed_docs.append(doc)

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunked_docs = splitter.split_documents(parsed_docs)

        logger.info(f"📦 Uploading {len(chunked_docs)} chunks to Pinecone")
        self.vectorstore.add_documents(chunked_docs)

        logger.info("✅ Schemes embedded and stored successfully")

    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})
        return retriever.invoke(query)
