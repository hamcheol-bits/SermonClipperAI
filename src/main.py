"""
단일 동영상 파일에서 설교 구간 추출
"""

import os
from src.analyzer import SermonVideoProcessor
from src.analyzer.config import INPUT_DIR, OUTPUT_DIR


def main():
    """
    단일 파일 처리 메인 함수
    """
    # 처리할 파일명 (필요시 변경)
    video_file = "성가교회 2026년 1월 14일 수요예배.mp4"
    input_path = os.path.join(INPUT_DIR, video_file)

    if not os.path.exists(input_path):
        print(f"❌ 파일이 없습니다: {input_path}")
        return

    print("🚀 SermonClipperAI 시작\n")

    # 프로세서 생성
    processor = SermonVideoProcessor()

    # 설교 구간 추출
    output_path = processor.extract_sermon_segment(input_path, OUTPUT_DIR)

    if output_path:
        info = processor.get_sermon_info()
        print(f"\n{'=' * 80}")
        print("✅ 추출 완료!")
        print(f"{'=' * 80}")
        print(f"📁 입력: {video_file}")
        print(f"📁 출력: {os.path.basename(output_path)}")
        print(f"⏱️  구간: {info['start_hms']} ~ {info['end_hms']}")
        print(f"⏱️  길이: {info['duration_minutes']:.1f}분")
        print(f"{'=' * 80}\n")
    else:
        print("\n❌ 설교 구간 추출에 실패했습니다.\n")


if __name__ == "__main__":
    main()