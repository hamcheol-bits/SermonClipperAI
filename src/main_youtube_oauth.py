#!/usr/bin/env python3
"""
YouTube Playlist URL Extractor (OAuth 2.0)
비공개 플레이리스트 포함 모든 플레이리스트 URL 추출
"""

from src.youtube import YouTubeAuthService, YouTubePlaylistService


def main():
    print("=" * 80)
    print("🎬 YouTube Playlist URL Extractor (OAuth 2.0)")
    print("=" * 80)

    try:
        # 1. 인증
        print("\n🔐 Step 1: OAuth 2.0 인증")
        print("-" * 80)
        auth_service = YouTubeAuthService()
        youtube = auth_service.get_youtube_service()

        # 2. 플레이리스트 서비스 생성
        print("\n📂 Step 2: 플레이리스트 서비스 초기화")
        print("-" * 80)
        playlist_service = YouTubePlaylistService(youtube)

        # 3. 내 플레이리스트 목록 표시
        playlists = playlist_service.print_playlists()

        if not playlists:
            print("\n⚠️  플레이리스트가 없습니다.")
            return

        # 4. 플레이리스트 선택
        print("=" * 80)
        print("\n처리할 플레이리스트를 선택하세요:")
        print("  • 번호 입력: 위 목록에서 번호 선택")
        print("  • ID 입력: 플레이리스트 ID 직접 입력")
        print("  • URL 입력: 플레이리스트 URL 붙여넣기")

        user_input = input("\n>>> ").strip()

        if not user_input:
            print("❌ 입력이 없습니다.")
            return

        # 플레이리스트 ID 추출
        if user_input.isdigit():
            # 번호로 선택
            idx = int(user_input) - 1
            if 0 <= idx < len(playlists):
                playlist_id = playlists[idx]['id']
                playlist_title = playlists[idx]['title']
            else:
                print("❌ 잘못된 번호입니다.")
                return
        elif 'list=' in user_input:
            # URL에서 ID 추출
            playlist_id = user_input.split('list=')[1].split('&')[0]
            playlist_title = None
        else:
            # 직접 ID 입력
            playlist_id = user_input
            playlist_title = None

        # 5. 영상 목록 가져오기
        print("\n" + "=" * 80)
        print("🎥 Step 3: 영상 목록 추출")
        print("-" * 80)

        videos = playlist_service.print_videos(playlist_id)

        if not videos:
            return

        # 6. 파일 저장 옵션
        print("=" * 80)
        save_option = input("\n파일로 저장하시겠습니까? (y/n): ").strip().lower()

        if save_option == 'y':
            # 기본 파일명 제안
            default_filename = f"{playlist_title.replace(' ', '_')}_urls.txt" if playlist_title else "playlist_urls.txt"
            filename = input(f"파일명 입력 (기본: {default_filename}): ").strip()

            if not filename:
                filename = default_filename

            playlist_service.export_urls_to_file(playlist_id, filename)

        print("\n" + "=" * 80)
        print("✅ 작업 완료!")
        print("=" * 80)

    except FileNotFoundError as e:
        print(f"\n{e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 작업을 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()