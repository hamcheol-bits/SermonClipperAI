"""
YouTube 플레이리스트 자동 처리 워크플로우
1. 플레이리스트 동영상 목록 조회
2. 각 동영상 다운로드 → 설교 구간 추출 → YouTube 업데이트
3. 진행상황 표시
"""

import os
from src.youtube import (
    YouTubeAuthService,
    YouTubePlaylistService,
    YouTubeDownloadService,
    YouTubeUpdateService
)
from src.analyzer import SermonVideoProcessor
from src.analyzer.config import INPUT_DIR, OUTPUT_DIR, BASE_DIR


def process_single_video(video_info, download_service, update_service, thumbnail_path):
    """
    단일 동영상 처리 파이프라인

    Args:
        video_info (dict): 동영상 정보 (video_id, url, title 등)
        download_service: YouTube 다운로드 서비스
        update_service: YouTube 업데이트 서비스
        thumbnail_path (str): 섬네일 이미지 경로

    Returns:
        bool: 성공 여부
    """
    video_id = video_info['video_id']
    video_url = video_info['url']
    video_title = video_info['title']

    print(f"\n{'=' * 80}")
    print(f"🎬 처리 중: {video_title}")
    print(f"   URL: {video_url}")
    print(f"{'=' * 80}\n")

    try:
        # ==========================================
        # 1. 동영상 다운로드
        # ==========================================
        print("📥 [Step 1/3] 동영상 다운로드 중...")
        downloaded_path = download_service.download_video(video_url, video_id)

        if not downloaded_path or not os.path.exists(downloaded_path):
            print(f"❌ 다운로드 실패: {video_title}")
            return False

        # ==========================================
        # 2. 설교 구간 추출 (SermonVideoProcessor 사용)
        # ==========================================
        print("\n🔍 [Step 2/3] 설교 구간 추출 중...")
        processor = SermonVideoProcessor()
        output_path = processor.extract_sermon_segment(downloaded_path, OUTPUT_DIR)

        if not output_path or not os.path.exists(output_path):
            print("❌ 설교 구간 추출 실패")
            cleanup_files(downloaded_path)
            return False

        # 추출 정보 출력
        info = processor.get_sermon_info()
        if info:
            print(f"\n📊 추출 정보:")
            print(f"   구간: {info['start_hms']} ~ {info['end_hms']}")
            print(f"   길이: {info['duration_minutes']:.1f}분")

        # ==========================================
        # 3. YouTube 업데이트 (삭제 후 재업로드)
        # ==========================================
        print("\n📤 [Step 3/3] YouTube 업데이트 중...")
        print("⚠️  기존 동영상을 삭제하고 새 동영상을 업로드합니다...")

        result = update_service.delete_and_reupload(
            video_id=video_id,
            new_video_path=output_path,
            thumbnail_path=thumbnail_path
        )

        if result:
            print(f"✅ YouTube 업데이트 완료!")
            print(f"   새 동영상 ID: {result['id']}")
        else:
            print("❌ YouTube 업데이트 실패")
            cleanup_files(downloaded_path, output_path)
            return False

        # ==========================================
        # 4. 파일 정리
        # ==========================================
        print("\n🗑️  임시 파일 삭제 중...")
        cleanup_files(downloaded_path, output_path)

        print(f"\n✅ '{video_title}' 처리 완료!\n")
        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_files(*file_paths):
    """
    임시 파일들 삭제

    Args:
        *file_paths: 삭제할 파일 경로들
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   삭제됨: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"   삭제 실패: {file_path} - {e}")


def main():
    """
    메인 워크플로우: 플레이리스트 전체 처리
    """
    print("\n" + "=" * 80)
    print("🚀 SermonClipperAI - YouTube Playlist Automation")
    print("=" * 80 + "\n")

    # ==========================================
    # 설정
    # ==========================================
    PLAYLIST_ID = input("플레이리스트 ID를 입력하세요: ").strip()

    if not PLAYLIST_ID:
        print("❌ 플레이리스트 ID가 필요합니다.")
        return

    THUMBNAIL_PATH = os.path.join(BASE_DIR, 'data', 'image', 'IMG_2010.JPG')

    # 섬네일 파일 확인
    if not os.path.exists(THUMBNAIL_PATH):
        print(f"⚠️  섬네일 파일을 찾을 수 없습니다: {THUMBNAIL_PATH}")
        use_thumbnail = input("섬네일 없이 진행하시겠습니까? (y/n): ").lower()
        if use_thumbnail != 'y':
            return
        THUMBNAIL_PATH = None

    # ==========================================
    # 1. YouTube 서비스 초기화
    # ==========================================
    print("🔐 YouTube 인증 중...")
    auth_service = YouTubeAuthService()
    youtube = auth_service.get_youtube_service()

    playlist_service = YouTubePlaylistService(youtube)
    download_service = YouTubeDownloadService(INPUT_DIR)
    update_service = YouTubeUpdateService(youtube)

    # ==========================================
    # 2. 플레이리스트 동영상 목록 가져오기
    # ==========================================
    print(f"\n📂 플레이리스트 정보 가져오는 중... (ID: {PLAYLIST_ID})")
    videos = playlist_service.get_playlist_videos(PLAYLIST_ID)

    if not videos:
        print("❌ 동영상을 찾을 수 없습니다.")
        return

    total_videos = len(videos)
    print(f"\n📊 총 {total_videos}개의 동영상을 처리합니다.\n")

    # ==========================================
    # 3. 각 동영상 처리
    # ==========================================
    success_count = 0
    fail_count = 0

    for idx, video in enumerate(videos, 1):
        progress = f"[{idx}/{total_videos}]"
        print(f"\n{'#' * 80}")
        print(f"진행 상황: {progress} ({success_count}개 성공, {fail_count}개 실패)")
        print(f"{'#' * 80}")

        success = process_single_video(
            video_info=video,
            download_service=download_service,
            update_service=update_service,
            thumbnail_path=THUMBNAIL_PATH
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

        # 진행률 표시
        percentage = (idx / total_videos) * 100
        print(f"\n📈 전체 진행률: {percentage:.1f}% ({idx}/{total_videos})")

    # ==========================================
    # 4. 최종 결과 요약
    # ==========================================
    print("\n" + "=" * 80)
    print("🎉 모든 작업 완료!")
    print("=" * 80)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 전체: {total_videos}개")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()