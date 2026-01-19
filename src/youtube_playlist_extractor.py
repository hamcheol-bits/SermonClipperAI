from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class YouTubePlaylistExtractor:
    """
    YouTube Data API를 이용하여 플레이리스트의 영상 URL 추출
    """

    def __init__(self, api_key=None):
        """
        Args:
            api_key (str): YouTube Data API 키 (None이면 .env에서 자동 로드)
        """
        # API 키 우선순위: 1) 매개변수 2) 환경변수
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')

        if not self.api_key:
            raise ValueError(
                "❌ API 키를 찾을 수 없습니다.\n"
                "   .env 파일에 YOUTUBE_API_KEY를 설정하거나\n"
                "   YouTubePlaylistExtractor(api_key='YOUR_KEY')로 직접 전달하세요."
            )

        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_playlist_videos(self, playlist_id, max_results=50):
        """
        플레이리스트의 모든 영상 정보 가져오기

        Args:
            playlist_id (str): 플레이리스트 ID (URL의 list= 뒤에 있는 값)
            max_results (int): 한 번에 가져올 최대 결과 수 (기본 50)

        Returns:
            list: 영상 정보 딕셔너리 리스트
        """
        videos = []
        next_page_token = None

        try:
            while True:
                # playlistItems API 호출
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=max_results,
                    pageToken=next_page_token
                )

                response = request.execute()

                # 영상 정보 추출
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_info = {
                        'video_id': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                        'position': item['snippet']['position'],
                        'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
                    }
                    videos.append(video_info)

                # 다음 페이지가 있는지 확인
                next_page_token = response.get('nextPageToken')

                if not next_page_token:
                    break

                print(f"📄 페이지 로드 중... (현재 {len(videos)}개 영상)")

            return videos

        except HttpError as e:
            print(f"❌ API 오류 발생: {e}")
            return []

    def print_video_urls(self, playlist_id):
        """
        플레이리스트의 영상 URL들을 출력

        Args:
            playlist_id (str): 플레이리스트 ID
        """
        print(f"\n🔍 플레이리스트 ID: {playlist_id}")
        print("=" * 80)

        videos = self.get_playlist_videos(playlist_id)

        if not videos:
            print("❌ 영상을 찾을 수 없습니다.")
            print("\n💡 확인 사항:")
            print("   1. 플레이리스트 ID가 올바른지 확인")
            print("   2. API 키가 유효한지 확인")
            print("   3. 플레이리스트가 비공개인 경우, OAuth 2.0 인증 필요")
            return []

        print(f"\n✅ 총 {len(videos)}개의 영상을 찾았습니다.\n")

        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   게시일: {video['published_at']}")
            print()

        return videos

    def export_urls_to_file(self, playlist_id, output_file='youtube_urls.txt'):
        """
        플레이리스트의 URL을 파일로 저장

        Args:
            playlist_id (str): 플레이리스트 ID
            output_file (str): 저장할 파일명
        """
        videos = self.get_playlist_videos(playlist_id)

        if not videos:
            print("❌ 저장할 영상이 없습니다.")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 플레이리스트 ID: {playlist_id}\n")
            f.write(f"# 총 영상 수: {len(videos)}\n\n")

            for video in videos:
                f.write(f"# {video['title']}\n")
                f.write(f"{video['url']}\n\n")

        print(f"✅ {len(videos)}개의 URL이 '{output_file}' 파일에 저장되었습니다.")


# ============================================================================
# 사용 예시
# ============================================================================

def main():
    # .env 파일에서 자동으로 API 키 로드
    extractor = YouTubePlaylistExtractor()

    # 플레이리스트 ID 입력
    # 예: https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx
    # 위 URL에서 list= 뒤의 값이 플레이리스트 ID입니다
    print("\n플레이리스트 URL 또는 ID를 입력하세요:")
    user_input = input(">>> ").strip()

    # URL에서 플레이리스트 ID 추출
    if 'list=' in user_input:
        PLAYLIST_ID = user_input.split('list=')[1].split('&')[0]
    else:
        PLAYLIST_ID = user_input

    print(f"\n플레이리스트 ID: {PLAYLIST_ID}\n")

    # 방법 1: 콘솔에 출력
    videos = extractor.print_video_urls(PLAYLIST_ID)

    if not videos:
        return

    # 방법 2: 파일로 저장
    save_file = input("\n파일로 저장하시겠습니까? (y/n): ").strip().lower()
    if save_file == 'y':
        filename = input("파일명 입력 (기본: sermon_urls.txt): ").strip() or 'sermon_urls.txt'
        extractor.export_urls_to_file(PLAYLIST_ID, filename)


if __name__ == "__main__":
    main()