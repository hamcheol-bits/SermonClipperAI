import chromadb
from chromadb.config import Settings
import uuid
from src.config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME

# Docker로 떠있는 ChromaDB에 HTTP로 접속
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

# 컬렉션이 있으면 가져오고 없으면 생성
collection = client.get_or_create_collection(name=COLLECTION_NAME)