from inaSpeechSegmenter import Segmenter
import pandas as pd
import warnings

# 경고 메시지 숨기기
warnings.filterwarnings("ignore")


def analyze_audio_structure(audio_path):
    print("🎧 [Audio-Analyzer] 소리 파형 분석 시작 (음악 vs 목소리)...")

    seg = Segmenter(vad_engine='smn', detect_gender=False)
    segmentation = seg(audio_path)

    df = pd.DataFrame(segmentation, columns=['label', 'start', 'end'])
    df['duration'] = df['end'] - df['start']

    return df


def find_sermon_candidates_by_audio(df, min_duration=1200, max_duration=3600, gap_threshold=60):
    """
    [설정 변경]
    - min_duration: 1200초 (20분)
    - max_duration: 3600초 (1시간)
    - gap_threshold: 60초 (말소리가 끊겨도 1분 이내면 같은 덩어리로 합침)
    """
    print(f"📊 [Audio-Analyzer] 설교 후보 구간 분석 (조건: {min_duration // 60}분 ~ {max_duration // 60}분)...")

    # Speech 구간만 추출하여 시작 시간순 정렬
    speech_df = df[df['label'] == 'speech'].sort_values(by='start').reset_index(drop=True)

    if speech_df.empty:
        print("❌ 'Speech' 구간이 전혀 감지되지 않았습니다.")
        return None, None

    # --- 1. 구간 병합 (Stitching) ---
    merged_blocks = []

    if not speech_df.empty:
        current_block = {
            'start': speech_df.loc[0, 'start'],
            'end': speech_df.loc[0, 'end']
        }

    for i in range(1, len(speech_df)):
        prev_end = current_block['end']
        curr_start = speech_df.loc[i, 'start']
        curr_end = speech_df.loc[i, 'end']

        gap = curr_start - prev_end

        if gap <= gap_threshold:
            current_block['end'] = curr_end  # 연장
        else:
            current_block['duration'] = current_block['end'] - current_block['start']
            merged_blocks.append(current_block)
            current_block = {'start': curr_start, 'end': curr_end}

    if 'start' in current_block:
        current_block['duration'] = current_block['end'] - current_block['start']
        merged_blocks.append(current_block)

    merged_df = pd.DataFrame(merged_blocks)

    # 디버깅용: 병합된 구간들 정보 출력
    # print("\n[병합된 말소리 덩어리 목록]")
    # for idx, row in merged_df.iterrows():
    #     print(f" - 후보 {idx+1}: {int(row['duration']/60)}분 ({int(row['start'])}초 ~ {int(row['end'])}초)")

    # --- 2. 조건 필터링 (20분 ~ 60분) ---
    # 우선순위 1: 20분 ~ 60분 사이인 구간
    perfect_candidates = merged_df[
        (merged_df['duration'] >= min_duration) &
        (merged_df['duration'] <= max_duration)
        ]

    final_pick = None

    if not perfect_candidates.empty:
        print(f"   ✅ 조건(20분~60분)을 만족하는 구간 {len(perfect_candidates)}개 발견!")
        # 그 중에서 가장 긴 것을 선택
        final_pick = perfect_candidates.loc[perfect_candidates['duration'].idxmax()]

    else:
        print("   ⚠️ 딱 20분~60분 사이인 구간이 없습니다. 차선책을 찾습니다.")

        # 차선책 1: 60분을 넘더라도, 20분 이상인 것 중 가장 "짧은" 것 (너무 긴 건 전체 예배일 수 있으므로)
        # 혹은 그냥 가장 긴 것을 설교로 간주
        long_candidates = merged_df[merged_df['duration'] >= min_duration]

        if not long_candidates.empty:
            print("   👉 1시간을 초과하지만 20분 이상인 구간을 선택합니다.")
            final_pick = long_candidates.loc[long_candidates['duration'].idxmax()]
        else:
            print("   ❌ 20분 이상인 말소리 구간이 없습니다. (설교가 아닐 수 있음)")
            # 어쩔 수 없이 전체 중 가장 긴 것 반환
            final_pick = merged_df.loc[merged_df['duration'].idxmax()]

    # 최종 결과 반환
    start_time = final_pick['start']
    end_time = final_pick['end']
    duration_min = final_pick['duration'] / 60

    print(f"   🎯 최종 선택 구간: {int(start_time)}초 ~ {int(end_time)}초 ({duration_min:.1f}분)")

    return start_time, end_time