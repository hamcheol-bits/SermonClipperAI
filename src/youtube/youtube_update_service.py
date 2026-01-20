"""
YouTube 동영상 업데이트 및 섬네일 관리 서비스
"""

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class YouTubeUpdateService:
    """
    YouTube 동영상 업데이트 및 섬네일 관리 서비스
    """

    def __init__(self, youtube_service):
        """
        Args:
            youtube_service: 인증된 YouTube API 서비스 객체
        """
        self.youtube = youtube_service

    def update_video(self, video_id, video_file_path, title=None, description=None):
        """
        기존 YouTube 동영상을 새 파일로 교체

        주의: YouTube API v3는 직접적인 동영상 파일 교체를 지원하지 않습니다.
        대신 메타데이터(제목, 설명, 태그 등)만 업데이트할 수 있습니다.
        동영상 파일 자체를 교체하려면 삭제 후 재업로드해야 합니다.

        Args:
            video_id (str): 업데이트할 동영상 ID
            video_file_path (str): 새 동영상 파일 경로
            title (str): 제목 (None이면 변경 안 함)
            description (str): 설명 (None이면 변경 안 함)

        Returns:
            dict: 업데이트된 동영상 정보
        """
        print(f"\n⚠️  YouTube API 제한사항:")
        print("   YouTube API v3는 기존 동영상 파일의 직접 교체를 지원하지 않습니다.")
        print("   동영상을 교체하려면:")
        print("   1. 기존 동영상 삭제")
        print("   2. 새 동영상 업로드")
        print("   또는 메타데이터만 업데이트합니다.\n")

        # 메타데이터 업데이트만 지원
        return self.update_video_metadata(video_id, title, description)

    def update_video_metadata(self, video_id, title=None, description=None, tags=None):
        """
        동영상 메타데이터 업데이트 (제목, 설명, 태그)

        Args:
            video_id (str): 동영상 ID
            title (str): 새 제목
            description (str): 새 설명
            tags (list): 새 태그 리스트

        Returns:
            dict: 업데이트된 동영상 정보
        """
        try:
            # 기존 동영상 정보 가져오기
            video_response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()

            if not video_response['items']:
                print(f"❌ 동영상을 찾을 수 없습니다: {video_id}")
                return None

            # 기존 정보에서 업데이트할 부분만 변경
            snippet = video_response['items'][0]['snippet']

            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags

            # 업데이트 요청
            update_response = self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            ).execute()

            print(f"✅ 동영상 메타데이터 업데이트 완료: {video_id}")
            return update_response

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 메타데이터 업데이트 실패: {e}")
            return None

    def update_thumbnail(self, video_id, thumbnail_path):
        """
        동영상 섬네일 이미지 변경

        Args:
            video_id (str): 동영상 ID
            thumbnail_path (str): 새 섬네일 이미지 파일 경로 (JPG, PNG)

        Returns:
            bool: 성공 여부
        """
        try:
            print(f"🖼️  섬네일 업로드 중: {video_id}")

            # 미디어 파일 업로드 준비
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/jpeg',
                resumable=True
            )

            # 섬네일 업데이트
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            )

            response = request.execute()

            print(f"✅ 섬네일 업데이트 완료!")
            print(f"   - 기본: {response['items'][0]['default']['url']}")

            return True

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            if e.resp.status == 403:
                print("   권한 오류: YouTube Data API에서 'youtube.upload' 스코프가 필요합니다.")
            return False
        except Exception as e:
            print(f"❌ 섬네일 업데이트 실패: {e}")
            return False

    def delete_and_reupload(self, video_id, new_video_path, thumbnail_path=None):
        """
        기존 동영상을 삭제하고 새 동영상을 업로드
        (동영상 파일 교체의 실질적인 방법)

        Args:
            video_id (str): 삭제할 동영상 ID
            new_video_path (str): 새로 업로드할 동영상 파일 경로
            thumbnail_path (str): 섬네일 이미지 경로 (선택사항)

        Returns:
            dict: 새로 업로드된 동영상 정보
        """
        try:
            # 1. 기존 동영상 정보 백업
            print("📋 기존 동영상 정보 백업 중...")
            video_response = self.youtube.videos().list(
                part='snippet,status',
                id=video_id
            ).execute()

            if not video_response['items']:
                print(f"❌ 동영상을 찾을 수 없습니다: {video_id}")
                return None

            old_snippet = video_response['items'][0]['snippet']
            old_status = video_response['items'][0]['status']

            # 2. 기존 동영상 삭제
            print(f"🗑️  기존 동영상 삭제 중: {video_id}")
            self.youtube.videos().delete(id=video_id).execute()
            print("✅ 삭제 완료")

            # 3. 새 동영상 업로드
            print(f"📤 새 동영상 업로드 중: {new_video_path}")

            body = {
                'snippet': {
                    'title': old_snippet['title'],
                    'description': old_snippet.get('description', ''),
                    'tags': old_snippet.get('tags', []),
                    'categoryId': old_snippet.get('categoryId', '22')  # 기본값: 22 (People & Blogs)
                },
                'status': {
                    'privacyStatus': old_status.get('privacyStatus', 'private')
                }
            }

            media = MediaFileUpload(
                new_video_path,
                mimetype='video/*',
                resumable=True
            )

            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status_upload, response = request.next_chunk()
                if status_upload:
                    progress = int(status_upload.progress() * 100)
                    print(f"   업로드 진행: {progress}%")

            new_video_id = response['id']
            print(f"✅ 업로드 완료! 새 동영상 ID: {new_video_id}")

            # 4. 섬네일 업데이트
            if thumbnail_path:
                self.update_thumbnail(new_video_id, thumbnail_path)

            return response

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 삭제 및 재업로드 실패: {e}")
            return None


# 사용 예시
if __name__ == "__main__":
    from .youtube_auth_service import YouTubeAuthService

    # 인증
    auth_service = YouTubeAuthService()
    youtube = auth_service.get_youtube_service()

    # 업데이트 서비스 생성
    update_service = YouTubeUpdateService(youtube)

    # 섬네일 변경 예시
    # update_service.update_thumbnail('VIDEO_ID', 'thumbnail.jpg')