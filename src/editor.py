import os
import subprocess


def cut_video(input_path, output_dir, start_time, end_time):
    # 출력 파일명 생성
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(output_dir, f"{name}_cut{ext}")

    print(f"✂️ [Editor] Cutting video from {start_time} to {end_time}...")

    # FFmpeg 명령어 구성
    # -ss: 시작 시간
    # -to: 종료 시간
    # -c copy: 재인코딩 없이 데이터만 복사 (속도 매우 빠름, 화질 저하 없음)
    command = [
        "ffmpeg", "-y",  # -y: 기존 파일 덮어쓰기
        "-i", input_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",
        output_path
    ]

    try:
        # FFmpeg 실행
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"🎉 [Done] Saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e}")
        # 실패 시 에러 로그 출력 (디버깅용)
        # print(e.stderr.decode())

    return output_path


def extract_audio(input_path, output_dir):
    """
    영상 파일에서 분석용 오디오(WAV, 16kHz, Mono) 추출
    """
    filename = os.path.basename(input_path)
    name, _ = os.path.splitext(filename)
    audio_path = os.path.join(output_dir, f"{name}.wav")

    # 이미 변환된 파일이 있으면 재사용
    if os.path.exists(audio_path):
        print(f"🔊 [Editor] Audio file already exists: {audio_path}")
        return audio_path

    print(f"🔊 [Editor] Extracting audio to {audio_path}...")

    # ffmpeg 옵션 설명:
    # -ac 1: Mono 채널 (분석 속도 향상)
    # -ar 16000: 16kHz 샘플링 (음성 분석 표준)
    # -vn: 비디오 제거
    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        audio_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Audio extraction complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Audio Extraction Error: {e}")
        return None

    return audio_path