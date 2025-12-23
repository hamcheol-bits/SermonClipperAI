import ollama
import json
import re
from .config import OLLAMA_MODEL


def find_cut_points(start_candidates, end_candidates):
    print("🧠 [Ollama] 검색된 문맥을 바탕으로 설교 구간 추론 중...")

    start_context = json.dumps(start_candidates, ensure_ascii=False)
    end_context = json.dumps(end_candidates, ensure_ascii=False)

    prompt = f"""
    You are a video editor. Find the start/end timestamps of the 'Sermon'.

    1. Start hint: "오늘 말씀", "성경 본문".
    2. End hint: "기도하겠습니다", "마치겠습시다".

    Context Start: {start_context}
    Context End: {end_context}

    OUTPUT JSON ONLY: {{"start": 120.5, "end": 2400.0}}
    """

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt},
        ])
        content = response['message']['content']

        # 정규표현식으로 JSON 추출
        code_block = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if code_block:
            json_str = code_block.group(1)
        else:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                print(f"❌ JSON 파싱 실패. 원본 응답:\n{content}")
                return None

        return json.loads(json_str)

    except Exception as e:
        print(f"❌ Ollama 통신/파싱 에러: {e}")
        return None