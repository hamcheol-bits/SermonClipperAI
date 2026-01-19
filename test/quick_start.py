#!/usr/bin/env python3
"""
YouTube Playlist Extractor - Quick Start (API Key Only)
API 키 방식 빠른 시작
"""

import os
from dotenv import load_dotenv

load_dotenv()


def check_setup():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인 중...\n")

    issues = []

    # 1. .env 파일 확인
    if not os.path.exists('../.env'):
        issues.append("❌ .env 파일이 없습니다.")
        print("   해결: .env.example을 복사하여 .env 파일을 만드세요.")
        print("   명령: cp .env.example .env\n")
    else:
        print("✅ .env 파일 존재")

    # 2. API 키 확인
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        issues.append("❌ YouTube API 키가 설정되지 않았습니다.")
        print("   해결: .env 파일에서 YOUTUBE_API_KEY를 실제 키로 변경하세요.\n")
    else:
        print("✅ YouTube API 키 설정됨")

    print("\n" + "=" * 60)

    if issues:
        print("\n⚠️  설정이 완료되지 않았습니다:")
        for issue in issues:
            print(f"   {issue}")
        print("\n📖 API 키 발급 방법:")
        print("   1. https://console.cloud.google.com/ 접속")
        print("   2. 프로젝트 생성")
        print("   3. YouTube Data API v3 활성화")
        print("   4. API 키 생성")
        print("   5. .env 파일에 키 입력")
        return False
    else:
        print("\n🎉 모든 설정이 완료되었습니다!")
        return True


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("🎬 YouTube Playlist URL Extractor (API Key)")
    print("=" * 60)

    # 설정 확인
    if not check_setup():
        print("\n설정을 완료한 후 다시 실행해주세요.")
        return

    try:
        from src.youtube_playlist_extractor import YouTubePlaylistExtractor

        # .env에서 자동으로 API 키 로드
        extractor = YouTubePlaylistExtractor()

        print("\n플레이리스트 URL 또는 ID를 입력하세요:")
        print("예시: https://www.youtube.com/playlist?list=PLxxxxxx")
        user_input = input("\n>>> ").strip()

        if not user_input:
            print("❌ 입력이 없습니다.")
            return

        # URL에서 플레이리스트 ID 추출
        if 'list=' in user_input:
            playlist_id = user_input.split('list=')[1].split('&')[0]
        else:
            playlist_id = user_input

        print(f"\n🔍 플레이리스트 분석 중... (ID: {playlist_id})")
        videos = extractor.print_video_urls(playlist_id)

        if not videos:
            return

        # 파일 저장 옵션
        print("\n" + "=" * 60)
        save = input("파일로 저장하시겠습니까? (y/n): ").strip().lower()

        if save == 'y':
            filename = input("파일명 입력 (기본: playlist_urls.txt): ").strip()
            if not filename:
                filename = 'playlist_urls.txt'

            extractor.export_urls_to_file(playlist_id, filename)

        print("\n✅ 완료!")

    except ValueError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()