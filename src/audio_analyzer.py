from inaSpeechSegmenter import Segmenter
import pandas as pd
import warnings

# 경고 메시지 숨기기 (TensorFlow 등에서 나오는 불필요한 로그)
warnings.filterwarnings("ignore")


def analyze_audio_structure(audio_path):
    print("🎧 [Audio-Analyzer] 소리 파형 분석 시작 (음악 vs 목소리)...")
    print("   (M1 Mac의 성능에 따라 1시간 영상 기준 약 1~3분 소요됩니다)")

    # vad_engine='smn' (Speech, Music, Noise)
    # detect_gender=False (남/녀 구분 안 함 -> 속도 향상)
    seg = Segmenter(vad_engine='smn', detect_gender=False)

    segmentation = seg(audio_path)

    # 결과를 사용하기 쉽게 DataFrame으로 변환
    df = pd.DataFrame(segmentation, columns=['label', 'start', 'end'])
    df['duration'] = df['end'] - df['start']

    return df


def find_sermon_candidates_by_audio(df, min_duration=600):
    """
    오디오 라벨 중 'speech'이면서 길이가 가장 긴 구간을 설교로 추정
    min_duration: 최소 10분(600초) 이상
    """
    print("📊 [Audio-Analyzer] 설교 후보 구간(Speech) 탐색 중...")

    # Speech 구간만 필터링
    speech_df = df[df['label'] == 'speech']

    if speech_df.empty:
        print("❌ 'Speech' 구간이 전혀 감지되지 않았습니다.")
        return None, None

    # 1. 10분 이상 지속된 말소리 구간 찾기
    candidates = speech_df[speech_df['duration'] > min_duration]

    if candidates.empty:
        print("⚠️ 10분 이상 지속된 Speech 구간이 없습니다. 가장 긴 Speech를 선택합니다.")
        best_row = speech_df.loc[speech_df['duration'].idxmax()]
    else:
        # 2. 후보군 중 가장 긴 Speech 구간을 설교로 간주
        # (보통 예배에서 기도가 10분을 넘기는 드물고, 설교가 가장 깁니다)
        best_row = candidates.loc[candidates['duration'].idxmax()]

    start_time = best_row['start']
    end_time = best_row['end']

    print(f"   👉 오디오 분석 추정 구간: {int(start_time)}초 ~ {int(end_time)}초 (길이: {best_row['duration'] / 60:.1f}분)")
    return start_time, end_time