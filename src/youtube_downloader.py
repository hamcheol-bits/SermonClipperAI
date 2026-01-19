import yt_dlp
import os
from .config import INPUT_DIR


def download_youtube_video(url, output_filename=None):
    """
    YouTube 영상을 다운로드하여 INPUT_DIR에 저장

    Args:
        url (str): YouTube 영상 URL
        output_filename (str): 저장할 파일명 (None이면 자동 생성)

    Returns:
        str: 다운로드된 파일 경로
    """

    # OUTPUT_DIR 생성 (없으면)
    os.makedirs(INPUT_DIR, exist_ok=True)

    # 파일명 설정
    if output_filename:
        # 확장자 제거 (yt-dlp가 자동으로 추가)
        output_template = os.path.join(INPUT_DIR, os.path.splitext(output_filename)[0])
    else:
        # 자동 파일명: 영상 제목 사용
        output_template = os.path.join(INPUT_DIR, '%(title)s.%(ext)s')

    # yt-dlp 옵션 설정
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # MP4 우선
        'outtmpl': output_template,
        'merge_output_format': 'mp4',  # 병합 시 MP4로
        'quiet': False,  # 진행 상황 표시
        'no_warnings': False,
    }

    try:
        print(f"📥 [YouTube Downloader] 다운로드 시작...")
        print(f"   URL: {url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 영상 정보 가져오기
            info = ydl.extract_info(url, download=True)

            # 다운로드된 파일 경로
            if output_filename:
                downloaded_file = output_template + '.mp4'
            else:
                downloaded_file = ydl.prepare_filename(info)

            print(f"✅ [YouTube Downloader] 다운로드 완료!")
            print(f"   저장 경로: {downloaded_file}")
            print(f"   영상 제목: {info.get('title', 'Unknown')}")
            print(f"   길이: {info.get('duration', 0) // 60}분")

            return downloaded_file

    except Exception as e:
        print(f"❌ [YouTube Downloader] 다운로드 실패: {e}")
        return None


def download_youtube_audio_only(url, output_filename=None):
    """
    YouTube 영상에서 오디오만 다운로드 (더 빠름)

    Args:
        url (str): YouTube 영상 URL
        output_filename (str): 저장할 파일명 (None이면 자동 생성)

    Returns:
        str: 다운로드된 파일 경로
    """
    os.makedirs(INPUT_DIR, exist_ok=True)

    if output_filename:
        output_template = os.path.join(INPUT_DIR, os.path.splitext(output_filename)[0])
    else:
        output_template = os.path.join(INPUT_DIR, '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
    }

    try:
        print(f"🎵 [YouTube Downloader] 오디오 다운로드 시작...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info) if not output_filename else output_template + '.m4a'

            print(f"✅ 오디오 다운로드 완료: {downloaded_file}")
            return downloaded_file

    except Exception as e:
        print(f"❌ 오디오 다운로드 실패: {e}")
        return None


# 사용 예시
if __name__ == "__main__":
    # 테스트용
    test_url = "https://www.youtube.com/watch?v=2PlgfX72Ca8"

    # 방법 1: 전체 영상 다운로드
    download_youtube_video(test_url, "test_sermon.mp4")

    # 방법 2: 오디오만 다운로드
    # download_youtube_audio_only(test_url, "test_audio.m4a")