import ollama
from .config import OLLAMA_MODEL


def classify_sequence(text_chunk):
    """
    텍스트 덩어리를 입력받아 [SONG, SERMON, PRAYER, OTHER] 중 하나로 분류
    """
    prompt = f"""
    Analyze the following transcript from a church service and classify it into one category.

    Categories:
    1. SONG: Lyrics of a hymn, choir singing, poetic expressions about praise.
    2. SERMON: Preaching, explaining Bible verses, speaking to the congregation.
    3. PRAYER: Speaking to God, supplication, ending with Amen.
    4. OTHER: Announcements, noise, silence.
    
    Specific Order of service near the sermon:
    1. SCRIPTURE: Reading Bible verses (Chapter/Verse mentions).
    2. CHOIR: Singing, Hymns, Lyrics (often poetic, or Whisper marks like ♪).
    3. SERMON: Preaching, Explaining scripture, Speaking to audience.
    4. PRAYER: Speaking to God (Lord, Father), Ending with Amen.

    Transcript: "{text_chunk}"

    OUTPUT ONLY THE CATEGORY NAME (e.g., SONG, SERMON, PRAYER). DO NOT EXPLAIN.
    """

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt},
        ])
        category = response['message']['content'].strip().upper()

        # 가끔 LLM이 잡담을 섞을 수 있으므로 정제
        if "SONG" in category: return "SONG"
        if "SERMON" in category: return "SERMON"
        if "PRAYER" in category: return "PRAYER"
        return "OTHER"

    except Exception as e:
        print(f"❌ Ollama 분류 에러: {e}")
        return "OTHER"