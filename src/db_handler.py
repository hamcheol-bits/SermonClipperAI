import chromadb
import uuid
from .config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME


class ChromaHandler:
    def __init__(self):
        # [Docker 모드] 서버에 http로 접속
        print(f"🔗 [ChromaDB] Docker Server 연결 시도: http://{CHROMA_HOST}:{CHROMA_PORT}...")
        try:
            self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            # 서버가 살아있는지 가벼운 핑 테스트
            self.client.heartbeat()
            print("✅ [ChromaDB] 서버 연결 성공!")
        except Exception as e:
            print(f"❌ [ChromaDB] 서버 연결 실패: {e}")
            print("👉 Docker가 켜져 있는지, 포트(8101)가 맞는지 확인해주세요.")
            raise e

        # 컬렉션 로드 (없으면 생성)
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    def save_segments(self, segments):
        print("📥 [ChromaDB] 텍스트 데이터 벡터화 및 저장 중...")

        # 기존 데이터 초기화 (해당 컬렉션 내 데이터만)
        if self.collection.count() > 0:
            ids = self.collection.get()['ids']
            if ids:
                self.collection.delete(ids=ids)

        ids = []
        documents = []
        metadatas = []

        for seg in segments:
            text = seg['text'].strip()
            if len(text) < 10: continue

            ids.append(str(uuid.uuid4()))
            documents.append(text)
            metadatas.append({"start": seg['start'], "end": seg['end']})

        # 배치 처리 (속도 및 안정성)
        batch_size = 100
        total = len(ids)
        for i in range(0, total, batch_size):
            self.collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )
        print(f"✅ [ChromaDB] 총 {total}개 문장 저장 완료.")

    def query_context(self, query_text, n_results=5):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )