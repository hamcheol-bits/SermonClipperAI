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