"""
YouTube OAuth 2.0 인증 서비스
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


class YouTubeAuthService:
    """
    YouTube OAuth 2.0 인증을 처리하는 서비스 클래스
    """

    # YouTube Data API 읽기 권한
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

    def __init__(self, credentials_file=None, token_file=None):
        """
        Args:
            credentials_file (str): OAuth 2.0 클라이언트 ID 파일 경로 (None이면 .env에서 로드)
            token_file (str): 인증 토큰 저장 파일 경로 (None이면 .env에서 로드)
        """
        # 파일 경로 설정 (우선순위: 매개변수 > 환경변수 > 기본값)
        self.credentials_file = (
                credentials_file or
                os.getenv('YOUTUBE_CREDENTIALS_FILE') or
                'credentials.json'
        )
        self.token_file = (
                token_file or
                os.getenv('YOUTUBE_TOKEN_FILE') or
                'token.pickle'
        )

        # credentials.json 파일 존재 확인
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"\n❌ OAuth 인증 파일을 찾을 수 없습니다: {self.credentials_file}\n\n"
                "📥 설정 방법:\n"
                "1. Google Cloud Console (https://console.cloud.google.com/) 접속\n"
                "2. OAuth 동의 화면 구성\n"
                "3. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)\n"
                "4. JSON 파일 다운로드\n"
                "5. 프로젝트 루트에 'credentials.json'으로 저장\n"
            )

        self._credentials = None

    def authenticate(self):
        """
        OAuth 2.0 인증 수행

        Returns:
            Credentials: 인증된 자격 증명
        """
        creds = None

        # 저장된 토큰이 있으면 로드
        if os.path.exists(self.token_file):
            print(f"🔑 저장된 토큰 로드 중... ({self.token_file})")
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # 유효한 자격 증명이 없으면 로그인 필요
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 토큰 갱신 중...")
                try:
                    creds.refresh(Request())
                    print("✅ 토큰 갱신 완료!")
                except Exception as e:
                    print(f"⚠️  토큰 갱신 실패: {e}")
                    print("   새로운 인증을 시작합니다...")
                    creds = None

            if not creds:
                print("\n🔐 OAuth 2.0 인증이 필요합니다.")
                print("   브라우저가 자동으로 열립니다.")
                print("   Google 계정으로 로그인하고 권한을 승인해주세요.\n")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

                print("✅ 인증 완료!")

            # 토큰 저장
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"💾 토큰 저장됨: {self.token_file}")
        else:
            print("✅ 유효한 인증 토큰 사용")

        self._credentials = creds
        return creds

    def get_youtube_service(self):
        """
        인증된 YouTube API 서비스 객체 반환

        Returns:
            Resource: YouTube API 서비스 객체
        """
        if not self._credentials:
            self.authenticate()

        return build('youtube', 'v3', credentials=self._credentials)

    def revoke_credentials(self):
        """
        저장된 인증 토큰 삭제 (재인증이 필요할 때 사용)
        """
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            print(f"🗑️  토큰 파일 삭제됨: {self.token_file}")
            self._credentials = None
            return True
        else:
            print("⚠️  삭제할 토큰 파일이 없습니다.")
            return False

    @property
    def is_authenticated(self):
        """
        현재 인증 상태 확인

        Returns:
            bool: 인증 여부
        """
        return self._credentials is not None and self._credentials.valid


# 사용 예시
if __name__ == "__main__":
    # 인증 서비스 생성
    auth_service = YouTubeAuthService()

    # 인증 수행
    auth_service.authenticate()

    # YouTube API 서비스 객체 가져오기
    youtube = auth_service.get_youtube_service()

    print("\n✅ YouTube API 서비스 준비 완료!")
    print(f"   인증 상태: {auth_service.is_authenticated}")