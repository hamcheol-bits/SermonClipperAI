import os
from src.transcriber import transcribe_video
from src.db_handler import ChromaHandler
from src.decision_maker import find_cut_points
from src.editor import cut_video
from src.config import INPUT_DIR, OUTPUT_DIR


def main():
    # 1. 파일 준비
    video_file = "1121.mp4"  # data/input 폴더 안에 넣어두세요
    input_path = os.path.join(INPUT_DIR, video_file)

    if not os.path.exists(input_path):
        print(f"파일이 없습니다: {input_path}")
        return

    # 2. Whisper로 텍스트 추출
    segments = transcribe_video(input_path)

    # 3. ChromaDB에 저장 (RAG 준비)
    db = ChromaHandler()
    db.save_segments(segments)

    # 4. RAG 검색 (설교 시작/끝 부분 찾기)
    # "설교 시작"과 관련된 멘트들을 쿼리로 던져서 후보군 추출
    start_docs = db.query_context("오늘 말씀, 성경 본문", n_results=10)
    end_docs = db.query_context("기도하겠습니다, 마치겠습니다", n_results=10)

    # 5. Ollama에게 판단 요청
    cut_points = find_cut_points(start_docs, end_docs)

    if cut_points:
        # 6. 영상 자르기
        cut_video(input_path, OUTPUT_DIR, cut_points['start'], cut_points['end'])
    else:
        print("구간을 찾지 못했습니다.")


if __name__ == "__main__":
    main()