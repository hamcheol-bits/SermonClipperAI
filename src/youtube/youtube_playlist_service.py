"""
YouTube 플레이리스트 관리 서비스
"""

from googleapiclient.errors import HttpError


class YouTubePlaylistService:
    """
    YouTube 플레이리스트 관련 기능을 처리하는 서비스 클래스
    """

    def __init__(self, youtube_service):
        """
        Args:
            youtube_service: 인증된 YouTube API 서비스 객체
        """
        self.youtube = youtube_service

    def get_my_playlists(self, max_results=50):
        """
        내 채널의 모든 플레이리스트 목록 가져오기

        Args:
            max_results (int): 한 번에 가져올 최대 결과 수

        Returns:
            list: 플레이리스트 정보 딕셔너리 리스트
        """
        playlists = []
        next_page_token = None

        try:
            print("📂 내 플레이리스트 목록 가져오는 중...")

            while True:
                request = self.youtube.playlists().list(
                    part='snippet,contentDetails,status',
                    mine=True,
                    maxResults=max_results,
                    pageToken=next_page_token
                )

                response = request.execute()

                for item in response.get('items', []):
                    playlist_info = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'privacy_status': item['status'].get('privacyStatus', 'unknown'),
                        'video_count': item['contentDetails']['itemCount'],
                        'published_at': item['snippet']['publishedAt']
                    }
                    playlists.append(playlist_info)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

                print(f"   페이지 로딩 중... (현재 {len(playlists)}개)")

            print(f"✅ 총 {len(playlists)}개의 플레이리스트를 찾았습니다.")
            return playlists

        except HttpError as e:
            print(f"❌ API 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"❌ 플레이리스트 목록 가져오기 실패: {e}")
            return []

    def get_playlist_videos(self, playlist_id, max_results=50):
        """
        플레이리스트의 모든 영상 정보 가져오기 (비공개 포함)

        Args:
            playlist_id (str): 플레이리스트 ID
            max_results (int): 한 번에 가져올 최대 결과 수

        Returns:
            list: 영상 정보 딕셔너리 리스트
        """
        videos = []
        next_page_token = None

        try:
            print(f"\n🎬 플레이리스트 영상 가져오는 중... (ID: {playlist_id})")

            while True:
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails,status',
                    playlistId=playlist_id,
                    maxResults=max_results,
                    pageToken=next_page_token
                )

                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    privacy_status = item['status'].get('privacyStatus', 'unknown')

                    video_info = {
                        'video_id': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                        'position': item['snippet']['position'],
                        'privacy_status': privacy_status,
                        'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
                    }
                    videos.append(video_info)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

                print(f"   페이지 로딩 중... (현재 {len(videos)}개)")

            print(f"✅ 총 {len(videos)}개의 영상을 찾았습니다.")
            return videos

        except HttpError as e:
            print(f"❌ API 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"❌ 영상 목록 가져오기 실패: {e}")
            return []

    def print_playlists(self, playlists=None):
        """
        플레이리스트 목록을 보기 좋게 출력

        Args:
            playlists (list): 플레이리스트 목록 (None이면 자동으로 가져옴)

        Returns:
            list: 플레이리스트 목록
        """
        if playlists is None:
            playlists = self.get_my_playlists()

        if not playlists:
            print("❌ 플레이리스트를 찾을 수 없습니다.")
            return []

        print("\n" + "=" * 80)
        print(f"📂 내 플레이리스트 목록 (총 {len(playlists)}개)")
        print("=" * 80 + "\n")

        for i, pl in enumerate(playlists, 1):
            # 공개 상태 아이콘
            status_icons = {
                'private': '🔒',
                'public': '🌐',
                'unlisted': '🔗'
            }
            status_icon = status_icons.get(pl['privacy_status'], '❓')

            print(f"{i}. {status_icon} {pl['title']}")
            print(f"   ID: {pl['id']}")
            print(f"   영상 수: {pl['video_count']}개")
            print(f"   상태: {pl['privacy_status']}")
            if pl['description']:
                desc_preview = pl['description'][:60] + '...' if len(pl['description']) > 60 else pl['description']
                print(f"   설명: {desc_preview}")
            print()

        return playlists

    def print_videos(self, playlist_id):
        """
        플레이리스트의 영상 목록을 보기 좋게 출력

        Args:
            playlist_id (str): 플레이리스트 ID

        Returns:
            list: 영상 목록
        """
        videos = self.get_playlist_videos(playlist_id)

        if not videos:
            print("❌ 영상을 찾을 수 없습니다.")
            return []

        print("\n" + "=" * 80)
        print(f"🎬 플레이리스트 영상 목록 (총 {len(videos)}개)")
        print("=" * 80 + "\n")

        for i, video in enumerate(videos, 1):
            # 공개 상태 아이콘
            status_icon = '🔒' if video['privacy_status'] == 'private' else '🌐'

            print(f"{i}. {status_icon} {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   상태: {video['privacy_status']}")
            print(f"   게시일: {video['published_at'][:10]}")
            print()

        return videos

    def export_urls_to_file(self, playlist_id, output_file='playlist_urls.txt'):
        """
        플레이리스트의 URL을 텍스트 파일로 저장

        Args:
            playlist_id (str): 플레이리스트 ID
            output_file (str): 저장할 파일명

        Returns:
            bool: 성공 여부
        """
        videos = self.get_playlist_videos(playlist_id)

        if not videos:
            print("❌ 저장할 영상이 없습니다.")
            return False

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 플레이리스트 ID: {playlist_id}\n")
                f.write(f"# 총 영상 수: {len(videos)}\n")
                f.write(f"# 생성 시간: {videos[0]['published_at'] if videos else 'N/A'}\n\n")

                for video in videos:
                    privacy_marker = "[비공개]" if video['privacy_status'] == 'private' else "[공개]"
                    f.write(f"# {privacy_marker} {video['title']}\n")
                    f.write(f"{video['url']}\n\n")

            print(f"\n✅ {len(videos)}개의 URL이 '{output_file}' 파일에 저장되었습니다.")
            return True

        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
            return False

    def get_playlist_by_name(self, playlist_name):
        """
        플레이리스트 이름으로 검색

        Args:
            playlist_name (str): 검색할 플레이리스트 이름

        Returns:
            dict or None: 찾은 플레이리스트 정보
        """
        playlists = self.get_my_playlists()

        for pl in playlists:
            if playlist_name.lower() in pl['title'].lower():
                return pl

        return None

    def get_private_playlists(self):
        """
        비공개 플레이리스트만 필터링

        Returns:
            list: 비공개 플레이리스트 목록
        """
        all_playlists = self.get_my_playlists()
        private_playlists = [pl for pl in all_playlists if pl['privacy_status'] == 'private']

        print(f"🔒 비공개 플레이리스트: {len(private_playlists)}개")
        return private_playlists


# 사용 예시
if __name__ == "__main__":
    from .youtube_auth_service import YouTubeAuthService

    # 1. 인증
    auth_service = YouTubeAuthService()
    youtube = auth_service.get_youtube_service()

    # 2. 플레이리스트 서비스 생성
    playlist_service = YouTubePlaylistService(youtube)

    # 3. 플레이리스트 목록 출력
    playlists = playlist_service.print_playlists()

    # 4. 첫 번째 플레이리스트의 영상 출력 (있다면)
    if playlists:
        playlist_service.print_videos(playlists[0]['id'])