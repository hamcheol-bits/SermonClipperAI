"""
설교 구간 추출을 위한 비디오 프로세서
오디오 분석 → STT → AI 분류 → 편집까지 전체 파이프라인 관리
"""

import datetime
from .transcriber import transcribe_video
from .audio_analyzer import analyze_audio_structure, find_sermon_candidates_by_audio
from .decision_maker import classify_sequence
from .editor import cut_video, extract_audio


class SermonVideoProcessor:
    """
    예배 영상에서 설교 구간을 추출하는 프로세서
    """

    def __init__(self):
        """프로세서 초기화"""
        self.segments = None
        self.rough_start = None
        self.rough_end = None
        self.final_start = None
        self.final_end = None

    @staticmethod
    def seconds_to_hms(seconds):
        """초를 시:분:초 형식으로 변환"""
        return str(datetime.timedelta(seconds=int(seconds)))

    def extract_sermon_segment(self, video_path, output_dir):
        """
        영상에서 설교 구간을 추출하는 전체 파이프라인

        Args:
            video_path (str): 입력 동영상 경로
            output_dir (str): 출력 디렉토리

        Returns:
            str: 추출된 동영상 경로 (실패 시 None)
        """
        print(f"\n🚀 설교 구간 추출 시작: {video_path}")

        # 1. 오디오 추출 및 분석
        audio_path = self._analyze_audio(video_path)
        if not audio_path:
            return None

        # 2. 음성 인식 (STT)
        self.segments = self._transcribe_audio(video_path)
        if not self.segments:
            return None

        # 3. AI 정밀 분석
        self._find_exact_boundaries()

        # 4. 영상 자르기
        output_path = self._cut_video(video_path, output_dir)

        return output_path

    def _analyze_audio(self, video_path):
        """
        오디오 추출 및 구조 분석

        Args:
            video_path (str): 동영상 파일 경로

        Returns:
            str: 오디오 파일 경로 (실패 시 None)
        """
        print("\n🔊 [1/4] 오디오 분석 중...")

        # 오디오 추출
        import os
        input_dir = os.path.dirname(video_path)
        audio_path = extract_audio(video_path, input_dir)

        if not audio_path:
            print("❌ 오디오 추출 실패")
            return None

        # 음악 vs 말소리 분석
        df_audio = analyze_audio_structure(audio_path)
        self.rough_start, self.rough_end = find_sermon_candidates_by_audio(df_audio)

        if self.rough_start is None:
            print("❌ 설교 구간을 찾을 수 없습니다.")
            return None

        print(f"\n📍 [1차 필터] 오디오 기반 구간: "
              f"{self.seconds_to_hms(self.rough_start)} ~ {self.seconds_to_hms(self.rough_end)}")

        return audio_path

    def _transcribe_audio(self, video_path):
        """
        Whisper를 사용한 음성 인식

        Args:
            video_path (str): 동영상 파일 경로

        Returns:
            list: 세그먼트 리스트 (실패 시 None)
        """
        print("\n🎙️  [2/4] 음성 인식 중...")

        try:
            segments = transcribe_video(video_path)
            print(f"✅ {len(segments)}개 세그먼트 인식 완료")
            return segments
        except Exception as e:
            print(f"❌ 음성 인식 실패: {e}")
            return None

    def _find_exact_boundaries(self):
        """
        Llama3를 사용한 정밀 경계 탐지
        """
        print("\n🤖 [3/4] AI 정밀 분석 중...")

        self.final_start = self._find_exact_boundary(
            self.segments, self.rough_start, direction='start'
        )
        self.final_end = self._find_exact_boundary(
            self.segments, self.rough_end, direction='end'
        )

        print(f"\n🎯 [최종 결과] 확정 구간: "
              f"{self.seconds_to_hms(self.final_start)} ~ {self.seconds_to_hms(self.final_end)}\n")

    def _find_exact_boundary(self, segments, rough_time, direction='start'):
        """
        오디오 분석으로 찾은 rough_time 근처를 Llama3로 정밀 검사

        Args:
            segments (list): Whisper 세그먼트 리스트
            rough_time (float): 대략적인 시간
            direction (str): 'start' 또는 'end'

        Returns:
            float: 정밀한 경계 시간
        """
        if not segments:
            return rough_time

        # rough_time에 가장 가까운 세그먼트 찾기
        center_idx = min(
            range(len(segments)),
            key=lambda i: abs(segments[i]['start'] - rough_time)
        )

        # 탐색 범위: 앞뒤 15개 세그먼트 (약 1분~1분30초)
        search_radius = 15
        start_idx = max(0, center_idx - search_radius)
        end_idx = min(len(segments), center_idx + search_radius)

        scan_type = "시작점" if direction == 'start' else "종료점"
        print(f"🔍 [Fine-Tuning] {scan_type} 정밀 탐색 "
              f"({self.seconds_to_hms(rough_time)} 근처)...")

        # 시작점 찾기
        if direction == 'start':
            return self._find_start_point(segments, start_idx, end_idx, rough_time)

        # 종료점 찾기
        elif direction == 'end':
            return self._find_end_point(segments, start_idx, end_idx, rough_time)

        return rough_time

    def _find_start_point(self, segments, start_idx, end_idx, fallback_time):
        """
        설교 시작점 찾기: "찬양/기타" → "설교"로 전환되는 지점

        Args:
            segments (list): 세그먼트 리스트
            start_idx (int): 탐색 시작 인덱스
            end_idx (int): 탐색 종료 인덱스
            fallback_time (float): 찾지 못했을 때 반환할 시간

        Returns:
            float: 설교 시작 시간
        """
        for i in range(start_idx, end_idx):
            # 3개 문장을 합쳐서 문맥 파악
            buffer = " ".join([
                s['text'] for s in segments[i:i + 3]
                if i + 3 < len(segments)
            ])
            category = classify_sequence(buffer)

            if category == "SERMON":
                # 연속 2번 이상 SERMON이면 확정 (오탐 방지)
                next_buffer = " ".join([
                    s['text'] for s in segments[i + 1:i + 4]
                    if i + 4 < len(segments)
                ])
                if classify_sequence(next_buffer) == "SERMON":
                    print(f"   ✅ 설교 시작 확정: {self.seconds_to_hms(segments[i]['start'])}")
                    return segments[i]['start']

        print("   ⚠️ 정밀 탐색 실패, 오디오 분석 시간 사용")
        return fallback_time

    def _find_end_point(self, segments, start_idx, end_idx, fallback_time):
        """
        설교 종료점 찾기: "설교" → "기도/찬양"으로 전환되는 지점

        Args:
            segments (list): 세그먼트 리스트
            start_idx (int): 탐색 시작 인덱스
            end_idx (int): 탐색 종료 인덱스
            fallback_time (float): 찾지 못했을 때 반환할 시간

        Returns:
            float: 설교 종료 시간
        """
        # 뒤에서부터 앞으로 탐색
        for i in range(end_idx, start_idx, -1):
            if i >= len(segments):
                continue

            # 이전 3문장 검사
            buffer_prev = " ".join([
                s['text'] for s in segments[i - 3:i]
                if i - 3 >= 0
            ])
            category_prev = classify_sequence(buffer_prev)

            if category_prev == "SERMON":
                # 현재 지점 바로 앞이 설교였다면 여기가 끝점
                cut_point = segments[i]['start']
                print(f"   ✅ 설교 종료 확정: {self.seconds_to_hms(cut_point)}")
                return cut_point

        print("   ⚠️ 정밀 탐색 실패, 오디오 분석 시간 사용")
        return fallback_time

    def _cut_video(self, video_path, output_dir):
        """
        확정된 구간으로 영상 자르기

        Args:
            video_path (str): 입력 동영상 경로
            output_dir (str): 출력 디렉토리

        Returns:
            str: 출력 파일 경로 (실패 시 None)
        """
        print("✂️  [4/4] 설교 구간 추출 중...")

        try:
            output_path = cut_video(
                video_path,
                output_dir,
                self.final_start,
                self.final_end
            )
            return output_path
        except Exception as e:
            print(f"❌ 영상 자르기 실패: {e}")
            return None

    def get_sermon_info(self):
        """
        추출된 설교 정보 반환

        Returns:
            dict: 설교 구간 정보
        """
        if not self.final_start or not self.final_end:
            return None

        duration = self.final_end - self.final_start

        return {
            'start_time': self.final_start,
            'end_time': self.final_end,
            'duration': duration,
            'start_hms': self.seconds_to_hms(self.final_start),
            'end_hms': self.seconds_to_hms(self.final_end),
            'duration_minutes': duration / 60
        }


# 사용 예시
if __name__ == "__main__":
    import os
    from .config import INPUT_DIR, OUTPUT_DIR

    # 프로세서 생성
    processor = SermonVideoProcessor()

    # 테스트 파일
    test_video = os.path.join(INPUT_DIR, "test.mp4")

    # 설교 구간 추출
    output_path = processor.extract_sermon_segment(test_video, OUTPUT_DIR)

    if output_path:
        info = processor.get_sermon_info()
        print(f"\n✅ 추출 완료!")
        print(f"   구간: {info['start_hms']} ~ {info['end_hms']}")
        print(f"   길이: {info['duration_minutes']:.1f}분")
        print(f"   출력: {output_path}")