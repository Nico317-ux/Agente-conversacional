from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage.sql import SQLStore
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_core.documents import Document
from typing import List, Dict
import hashlib

class RAGProcessor:
    def __init__(self,
                top_k: int,
                score_threshold: float,
                vector_db_path: str,
                hf_token: str,
                provider: str,
                db_path_cache: str,
                name_model: str):
    
        self.top_k = top_k
        self.score_threshold = score_threshold
        underlying_embeddings = HuggingFaceEndpointEmbeddings(
            model= name_model,
            task='feature-extraction',
            huggingfacehub_api_token= hf_token,
            provider= provider
        )

        def sha256_encoder(key: str) -> str:
            return hashlib.sha256(key.strip().lower().encode()).hexdigest()
        
        cache_sql_url = f'sqlite:///{db_path_cache}'
        store = SQLStore(namespace = 'embeddings_cache',
                         db_url = cache_sql_url,
                        )
        self.embeddings = CacheBackedEmbeddings.from_bytes_store(
            underlying_embeddings,
            store,
            key_encoder= sha256_encoder
        )

        self.vectorstore = Chroma(
            persist_directory=vector_db_path,
            embedding_function=self.embeddings,
            collection_name="wikipedia_rag"
        )

        base_retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": top_k}
        )

        embeddings_filter = EmbeddingsFilter(
            embeddings=self.embeddings,
            similarity_threshold=score_threshold
        )
        
        self.retriever = ContextualCompressionRetriever(
            base_compressor=embeddings_filter,
            base_retriever=base_retriever
        )
        
    def retrieve_relevant_chucks(self, query: str) -> List[Dict]:
        documents = self.retriever.invoke(query)

        relevant_chunks = []
        for doc in documents:
            score = self.calculate_score(doc)
            relevant_chunks.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': score
            })
        
        relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
        return relevant_chunks
    
    def calculate_score(self, doc: Document) -> float:
        return doc.metadata.get('score', 1.0)
    
    def format_context(self, chunks: List[Dict]) -> str:
        context = 'Relevant information found: \n'
        for i, chunk in enumerate(chunks, 1):
            context += f'Fragment: {i} (score: {chunk['score']:.2f}): \n'
            context += f'Title: {chunk['metadata']}\n'
            context += f'Content: {chunk['content']}\n\n'
        return context.strip()