"""
YouTube 동영상 다운로드 서비스
"""

import os
import yt_dlp


class YouTubeDownloadService:
    """
    yt-dlp를 사용한 YouTube 동영상 다운로드 서비스
    """

    def __init__(self, download_dir):
        """
        Args:
            download_dir (str): 다운로드할 디렉토리 경로
        """
        self.download_dir = download_dir

        # 디렉토리가 없으면 생성
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def download_video(self, video_url, video_title=None):
        """
        YouTube 동영상을 다운로드

        Args:
            video_url (str): YouTube 동영상 URL
            video_title (str): 저장할 파일명 (None이면 자동 생성)

        Returns:
            str: 다운로드된 파일 경로 (실패 시 None)
        """
        try:
            # 파일명 설정
            if video_title:
                # 파일명으로 사용할 수 없는 문자 제거
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
                output_template = os.path.join(self.download_dir, f"{safe_title}.%(ext)s")
            else:
                output_template = os.path.join(self.download_dir, '%(title)s.%(ext)s')

            # yt-dlp 옵션
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
            }

            print(f"📥 다운로드 시작: {video_url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 영상 정보 추출
                info = ydl.extract_info(video_url, download=True)

                # 다운로드된 파일 경로 확인
                if video_title:
                    downloaded_file = os.path.join(self.download_dir, f"{safe_title}.mp4")
                else:
                    downloaded_file = ydl.prepare_filename(info)

                if os.path.exists(downloaded_file):
                    print(f"✅ 다운로드 완료: {downloaded_file}")
                    return downloaded_file
                else:
                    print(f"❌ 파일을 찾을 수 없습니다: {downloaded_file}")
                    return None

        except Exception as e:
            print(f"❌ 다운로드 실패: {e}")
            return None

    def get_video_info(self, video_url):
        """
        다운로드 없이 동영상 정보만 가져오기

        Args:
            video_url (str): YouTube 동영상 URL

        Returns:
            dict: 동영상 정보
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'description': info.get('description'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                }

        except Exception as e:
            print(f"❌ 정보 가져오기 실패: {e}")
            return None


# 사용 예시
if __name__ == "__main__":
    download_service = YouTubeDownloadService('./downloads')

    # 테스트 URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # 동영상 정보만 가져오기
    info = download_service.get_video_info(test_url)
    if info:
        print(f"제목: {info['title']}")
        print(f"길이: {info['duration']}초")

    # 다운로드
    # downloaded_path = download_service.download_video(test_url)