import os
import datetime
from src.transcriber import transcribe_video
from src.analytics import find_longest_speech_block
from src.decision_maker import classify_sequence
from src.editor import cut_video
from src.config import INPUT_DIR, OUTPUT_DIR


def seconds_to_hms(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def find_real_start(segments, rough_start_idx):
    """
    [Start-Search] 블록 시작점(rough_start_idx)부터 정방향으로 가면서
    SONG/SCRIPTURE/OTHER 등을 건너뛰고 'SERMON'이 나오는 순간을 포착
    """
    print("🔍 [Start-Search] 찬양/성경 건너뛰고 설교 시작점 찾기 (Forward Scan)...")

    # 안전장치: 시작점을 살짝만 앞(1분 전, 약 10문장)으로 당김. 50문장은 너무 멉니다.
    search_start = max(0, rough_start_idx - 10)
    limit = min(len(segments), rough_start_idx + 200)

    consecutive_sermon_count = 0

    for i in range(search_start, limit):
        # 3문장씩 묶어서 문맥 판단
        buffer = " ".join([s['text'] for s in segments[i:i + 3]])
        category = classify_sequence(buffer)

        time_str = seconds_to_hms(segments[i]['start'])

        if i % 10 == 0:  # 로그 너무 많으면 보기 힘드니 10개마다 찍음
            print(f"   Testing [{time_str}] : {category}")

        if category == "SERMON":
            consecutive_sermon_count += 1
            # "이거 설교다"라고 3번 연속 확신하면 그 지점을 시작점으로
            if consecutive_sermon_count >= 3:
                # 3번 연속의 첫 번째가 시작점
                real_start_idx = i - 2
                print(f"   🚀 설교 시작 확정! -> {seconds_to_hms(segments[real_start_idx]['start'])}")
                return segments[real_start_idx]['start']
        else:
            # 찬양, 성경봉독 등이 나오면 카운트 리셋 (설교 아님)
            consecutive_sermon_count = 0

    # 못 찾으면 원래 블록 시작점 반환
    return segments[rough_start_idx]['start']


def find_real_end(segments, rough_end_idx):
    """
    [End-Search] 블록 끝점부터 역방향으로 들어오며
    SONG/PRAYER/OTHER 등을 건너뛰고 'SERMON'이 끝나는 지점 포착
    """
    print("🔍 [End-Search] 설교 후 기도/찬양 건너뛰기 (Backward Scan)...")

    # 끝점에서 안쪽으로 탐색
    # 이번에는 조금 여유있게 뒤에서부터 봐도 됨
    search_start = min(len(segments) - 1, rough_end_idx + 10)
    limit = max(0, rough_end_idx - 300)

    for i in range(search_start, limit, -1):
        buffer = " ".join([s['text'] for s in segments[i:i + 3]])
        category = classify_sequence(buffer)

        time_str = seconds_to_hms(segments[i]['start'])
        if i % 10 == 0:
            print(f"   Testing [{time_str}] : {category}")

        # 거꾸로 탐색하다가 'SERMON'을 만났다는 것은
        # 그 바로 뒤(i+1)까지가 기도/찬양/광고였다는 뜻 -> 거기가 자르는 포인트
        if category == "SERMON":
            cut_point = segments[i + 1]['start']
            print(f"   🏁 설교 끝 지점 발견 (뒤에는 {classify_sequence(segments[i + 1]['text'])}) -> {seconds_to_hms(cut_point)}")
            return cut_point

    return segments[rough_end_idx]['end']


def main():
    video_file = "1121.mp4"
    input_path = os.path.join(INPUT_DIR, video_file)

    if not os.path.exists(input_path):
        print(f"파일이 없습니다: {input_path}")
        return

    # 1. STT 수행
    segments = transcribe_video(input_path)

    # 2. 가장 긴 덩어리 찾기 (Gap 20초)
    # [성경+찬양+설교+기도+광고]가 하나로 뭉쳐서 나옴
    longest_block = find_longest_speech_block(segments, gap_threshold=20.0, min_duration=600)

    if not longest_block:
        print("❌ 구간을 찾지 못했습니다.")
        return

    print(f"\n📍 1차 뭉치 구간: {seconds_to_hms(longest_block['start'])} ~ {seconds_to_hms(longest_block['end'])}")

    # 3. 인덱스 찾기
    start_idx = next(i for i, s in enumerate(segments) if s['start'] == longest_block['start'])
    end_idx = next(i for i, s in enumerate(segments) if s['end'] == longest_block['end'])

    # 4. 정밀 탐색 (범위 수정됨: -50 대신 -10 사용)
    # 핵심 변경: start_idx 근처(22분)부터 탐색해야 찬양(Song)을 건너뛰고 설교(24분)를 만남.
    # 15분(기도)까지 가지 않음.
    final_start = find_real_start(segments, start_idx)

    final_end = find_real_end(segments, end_idx)

    print(f"\n🎯 최종 확정 구간: {seconds_to_hms(final_start)} ~ {seconds_to_hms(final_end)}\n")

    # 5. 자르기
    cut_video(input_path, OUTPUT_DIR, final_start, final_end)


if __name__ == "__main__":
    main()