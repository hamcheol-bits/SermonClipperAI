def find_longest_speech_block(segments, gap_threshold=3.0, min_duration=600):
    """
    segments: Whisper 결과 리스트
    gap_threshold: 문장 사이 공백이 이 초(sec)보다 작으면 같은 블록으로 간주 (기본 3초)
    min_duration: 최소 이 초(sec) 이상이어야 설교로 인정 (기본 600초 = 10분)
    """
    print("📊 [Analytics] 가장 긴 연속 발화 구간(설교)을 계산 중...")

    if not segments:
        return None

    blocks = []
    # 첫 번째 블록 초기화
    current_block = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'text_len': len(segments[0]['text'])
    }

    for i in range(1, len(segments)):
        prev = segments[i - 1]
        curr = segments[i]

        # 이전 문장 끝과 현재 문장 시작 사이의 공백 계산
        gap = curr['start'] - prev['end']

        if gap <= gap_threshold:
            # 공백이 짧으면 같은 덩어리로 합침 (설교가 이어지는 중)
            current_block['end'] = curr['end']
            current_block['text_len'] += len(curr['text'])
        else:
            # 공백이 길면(찬양 간주, 사회자 교체 등) 블록 끊고 새로 시작
            blocks.append(current_block)
            current_block = {
                'start': curr['start'],
                'end': curr['end'],
                'text_len': len(curr['text'])
            }

    # 마지막 블록 추가
    blocks.append(current_block)

    # 1. 덩어리 중에서 '시간 길이(Duration)'가 가장 긴 것 찾기
    # (단, 텍스트 길이도 어느 정도 있어야 함 - 노이즈 방지)
    valid_blocks = [b for b in blocks if (b['end'] - b['start']) > min_duration]

    if not valid_blocks:
        print("⚠️ 10분 이상 지속된 구간이 없습니다. 기준을 낮춰서 다시 찾습니다.")
        valid_blocks = blocks

    # 시간 순으로 정렬하여 가장 긴 블록 리턴
    longest_block = max(valid_blocks, key=lambda x: x['end'] - x['start'])

    duration_min = (longest_block['end'] - longest_block['start']) / 60
    print(f"🎯 [Found] 가장 유력한 설교 구간 발견: {duration_min:.1f}분 동안 지속됨")

    return longest_block