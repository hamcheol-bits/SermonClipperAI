import datetime

def find_longest_speech_block(segments, gap_threshold=20.0, min_duration=600):
    """
    gap_threshold: 3.0 -> 20.0 (설교 중 긴 침묵도 같은 덩어리로 인식)
    """
    print("📊 [Analytics] 가장 긴 연속 발화 구간(설교)을 계산 중...")

    if not segments:
        return None

    blocks = []
    current_block = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'text_len': len(segments[0]['text'])
    }

    for i in range(1, len(segments)):
        prev = segments[i - 1]
        curr = segments[i]

        # gap 계산
        gap = curr['start'] - prev['end']

        # 20초 이내의 공백은 같은 설교로 간주
        if gap <= gap_threshold:
            current_block['end'] = curr['end']
            current_block['text_len'] += len(curr['text'])
        else:
            blocks.append(current_block)
            current_block = {
                'start': curr['start'],
                'end': curr['end'],
                'text_len': len(curr['text'])
            }

    blocks.append(current_block)

    valid_blocks = [b for b in blocks if (b['end'] - b['start']) > min_duration]
    if not valid_blocks:
        print("⚠️ 10분 이상 지속된 구간이 없습니다. 기준을 낮춰서 다시 찾습니다.")
        valid_blocks = blocks

    longest_block = max(valid_blocks, key=lambda x: x['end'] - x['start'])

    duration_min = (longest_block['end'] - longest_block['start']) / 60
    print(f"   - 구간: {seconds_to_hms(longest_block['start'])} ~ {seconds_to_hms(longest_block['end'])}")
    print(f"   - 길이: {duration_min:.1f}분")

    return longest_block

def seconds_to_hms(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))