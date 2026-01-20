import os
import datetime
from src.transcriber import transcribe_video
from src.audio_analyzer import analyze_audio_structure, find_sermon_candidates_by_audio  # <-- 신규 로직
from src.decision_maker import classify_sequence
from src.editor import cut_video, extract_audio
from src.config import INPUT_DIR, OUTPUT_DIR


def seconds_to_hms(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def find_exact_boundary(segments, rough_time, direction='start'):
    """
    오디오 분석으로 찾은 rough_time 근처(앞뒤 60초)만 Llama3로 정밀 검사
    direction: 'start'면 설교 시작점, 'end'면 설교 끝점 찾기
    """
    # rough_time에 가장 가까운 세그먼트 인덱스 찾기
    if not segments:
        return rough_time

    center_idx = min(range(len(segments)), key=lambda i: abs(segments[i]['start'] - rough_time))

    # 탐색 범위: Whisper 세그먼트 기준 앞뒤 15개 (약 1분~1분30초 범위)
    search_radius = 15
    start_idx = max(0, center_idx - search_radius)
    end_idx = min(len(segments), center_idx + search_radius)

    scan_type = "시작점" if direction == 'start' else "종료점"
    print(f"🔍 [Fine-Tuning] {scan_type} 정밀 탐색 ({seconds_to_hms(rough_time)} 근처)...")

    # 1. 시작점 찾기: "찬양/기타" -> "설교"로 바뀌는 순간
    if direction == 'start':
        for i in range(start_idx, end_idx):
            # 문맥 파악을 위해 3문장 합침
            buffer = " ".join([s['text'] for s in segments[i:i + 3] if i + 3 < len(segments)])
            category = classify_sequence(buffer)

            # 디버깅용 로그 (필요시 주석 해제)
            # print(f"   Testing [{seconds_to_hms(segments[i]['start'])}] : {category}")

            if category == "SERMON":
                # 연속 2번 이상 SERMON이면 확정 (오탐 방지)
                next_buffer = " ".join([s['text'] for s in segments[i + 1:i + 4] if i + 4 < len(segments)])
                if classify_sequence(next_buffer) == "SERMON":
                    print(f"   ✅ 설교 시작 확정: {seconds_to_hms(segments[i]['start'])}")
                    return segments[i]['start']

        # 못 찾으면 오디오 분석 결과 그대로 반환
        print("   ⚠️ 정밀 탐색 실패, 오디오 분석 시간 사용")
        return rough_time

    # 2. 끝점 찾기: "설교" -> "기도/찬양"으로 바뀌는 순간
    elif direction == 'end':
        # 뒤에서부터 앞으로 오면서 SERMON이 끝나는 곳 찾기
        for i in range(end_idx, start_idx, -1):
            if i >= len(segments): continue

            # 이전 3문장을 검사
            buffer_prev = " ".join([s['text'] for s in segments[i - 3:i] if i - 3 >= 0])
            category_prev = classify_sequence(buffer_prev)

            if category_prev == "SERMON":
                # 현재 지점 바로 앞이 설교였다면, 여기가 끝점
                cut_point = segments[i]['start']
                print(f"   ✅ 설교 종료 확정: {seconds_to_hms(cut_point)}")
                return cut_point

        print("   ⚠️ 정밀 탐색 실패, 오디오 분석 시간 사용")
        return rough_time


def main():
    video_file = "성가교회 2026년 1월 14일 수요예배.mp4"  # 처리할 파일명 (필요시 변경)
    input_path = os.path.join(INPUT_DIR, video_file)

    if not os.path.exists(input_path):
        print(f"파일이 없습니다: {input_path}")
        return

    print("🚀 SermonClipperAI 시작 (Audio Analysis + AI Mode)")

    # -----------------------------------------
    # 1. 오디오 추출 및 구조 분석 (가장 중요)
    # -----------------------------------------
    audio_path = extract_audio(input_path, INPUT_DIR)
    if not audio_path: return

    # 음악(Music) vs 말소리(Speech) 분석
    df_audio = analyze_audio_structure(audio_path)

    # 대략적인 설교 구간(가장 긴 말소리) 추출
    rough_start, rough_end = find_sermon_candidates_by_audio(df_audio)

    if rough_start is None:
        print("❌ 설교 구간을 찾을 수 없습니다.")
        return

    print(f"\n📍 [1차 필터] 오디오 기반 구간: {seconds_to_hms(rough_start)} ~ {seconds_to_hms(rough_end)}")

    # -----------------------------------------
    # 2. Whisper STT (전체 텍스트 확보)
    # -----------------------------------------
    # M1 Mac에서는 Whisper 속도가 빠르므로 전체 변환 후 매칭하는 것이 정확도 면에서 유리합니다.
    segments = transcribe_video(input_path)

    # -----------------------------------------
    # 3. Llama3 정밀 보정 (Fine-Tuning)
    # -----------------------------------------
    # 오디오로 찾은 시간 앞뒤를 LLM이 텍스트로 읽어보며 1~2초 단위 미세 조정
    final_start = find_exact_boundary(segments, rough_start, direction='start')
    final_end = find_exact_boundary(segments, rough_end, direction='end')

    print(f"\n🎯 [최종 결과] 확정 구간: {seconds_to_hms(final_start)} ~ {seconds_to_hms(final_end)}\n")

    # -----------------------------------------
    # 4. 영상 자르기
    # -----------------------------------------
    cut_video(input_path, OUTPUT_DIR, final_start, final_end)


if __name__ == "__main__":
    main()