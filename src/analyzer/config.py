import os

# Ollama 설정
OLLAMA_MODEL = "llama3.1:8b"  # 사용 중인 모델명

# ChromaDB 설정 (도커 컨테이너 정보 반영)
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001  # 사용자의 포트 8101 반영
COLLECTION_NAME = "sermon_transcripts"

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'output')