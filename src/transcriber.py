import whisper
import torch


def transcribe_video(video_path):
    # Apple Silicon(MPS) 가속 사용
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"🚀 [Whisper] Using device: {device}")

    print("⏳ [Whisper] Loading model...")
    model = whisper.load_model("medium", device=device)

    print("🎙️ [Whisper] Transcribing audio...")
    result = model.transcribe(video_path, language="ko", fp16=False)

    return result['segments']  # {start, end, text} 리스트 반환