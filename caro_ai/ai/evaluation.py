# evaluation.py – Quét toàn bộ bàn cờ (hàng, cột, chéo), phát hiện mọi pattern

WEIGHTS = {
    "WIN":        10_000_000,
    "LOSS":      -10_000_000,
    "OPEN_FIVE":   1_000_000,
    "DEAD_FIVE":     100_000,
    "OPEN_FOUR":     100_000,
    "DEAD_FOUR":      10_000,
    "OPEN_THREE":     10_000,
    "DEAD_THREE":      1_000,
    "OPEN_TWO":         500,
    "DEAD_TWO":          50,
}

def evaluate(board, player, last_move=None):
    """
    Đánh giá toàn bộ bàn cờ từ góc nhìn player.
    last_move không dùng nữa – quét hết để không bỏ lỡ đe dọa từ xa.
    """
    opponent = 'O' if player == 'X' else 'X'
    size = board.size
    grid = board.grid
    player_score = 0
    opponent_score = 0

    # Duyệt hàng ngang
    for r in range(size):
        line = ''.join(grid[r][c] for c in range(size))
        p, o = _score_line(line, player, opponent)
        player_score += p
        opponent_score += o

    # Duyệt hàng dọc
    for c in range(size):
        line = ''.join(grid[r][c] for r in range(size))
        p, o = _score_line(line, player, opponent)
        player_score += p
        opponent_score += o

    # Duyệt chéo chính (top-left -> bottom-right)
    for start in range(-size+1, size):
        diag = []
        for i in range(size):
            r, c = i, i - start
            if 0 <= c < size:
                diag.append(grid[r][c])
        if len(diag) >= 5:
            line = ''.join(diag)
            p, o = _score_line(line, player, opponent)
            player_score += p
            opponent_score += o

    # Duyệt chéo phụ (top-right -> bottom-left)
    for start in range(0, 2*size - 1):
        diag = []
        for i in range(size):
            r, c = i, start - i
            if 0 <= c < size:
                diag.append(grid[r][c])
        if len(diag) >= 5:
            line = ''.join(diag)
            p, o = _score_line(line, player, opponent)
            player_score += p
            opponent_score += o

    # Nếu đối thủ có cơ hội thắng ngay (open five) -> thua tuyệt đối
    if opponent_score >= WEIGHTS["OPEN_FIVE"]:
        return WEIGHTS["LOSS"]
    # Nếu player có thể thắng ngay -> thắng tuyệt đối
    if player_score >= WEIGHTS["OPEN_FIVE"]:
        return WEIGHTS["WIN"]

    # Ưu tiên chặn open four của đối thủ (rất gần thắng)
    if opponent_score >= WEIGHTS["OPEN_FOUR"]:
        return WEIGHTS["LOSS"] // 2 + opponent_score
    # Ưu tiên chặn open three
    if opponent_score >= WEIGHTS["OPEN_THREE"]:
        return player_score - 5 * opponent_score
    # Bình thường
    return player_score - 2 * opponent_score


def _score_line(line, player, opponent):
    """Tính điểm cho player và opponent trên một dòng (chuỗi)."""
    # Thay ký tự để dễ tìm pattern
    p_line = line.replace(player, 'P').replace(opponent, 'E')
    o_line = line.replace(opponent, 'P').replace(player, 'E')

    def _count(ln):
        score = 0
        # 5 quân liên tiếp (thắng)
        if 'PPPPP' in ln:
            # Xác định open hay dead
            idx = ln.find('PPPPP')
            left = ln[idx-1] if idx > 0 else '#'
            right = ln[idx+5] if idx+5 < len(ln) else '#'
            if left == '.' and right == '.':
                score += WEIGHTS["OPEN_FIVE"]
            else:
                score += WEIGHTS["DEAD_FIVE"]
        # 4 quân
        elif 'PPPP' in ln:
            idx = ln.find('PPPP')
            left = ln[idx-1] if idx > 0 else '#'
            right = ln[idx+4] if idx+4 < len(ln) else '#'
            if left == '.' and right == '.':
                score += WEIGHTS["OPEN_FOUR"]
            else:
                score += WEIGHTS["DEAD_FOUR"]
        # 3 quân
        elif 'PPP' in ln:
            idx = ln.find('PPP')
            left = ln[idx-1] if idx > 0 else '#'
            right = ln[idx+3] if idx+3 < len(ln) else '#'
            if left == '.' and right == '.':
                score += WEIGHTS["OPEN_THREE"]
            else:
                # Kiểm tra broken three (có dấu chấm giữa)
                if 'P.PP' in ln or 'PP.P' in ln:
                    score += WEIGHTS["OPEN_THREE"]  # vẫn nguy hiểm
                else:
                    score += WEIGHTS["DEAD_THREE"]
        # 2 quân
        elif 'PP' in ln:
            idx = ln.find('PP')
            left = ln[idx-1] if idx > 0 else '#'
            right = ln[idx+2] if idx+2 < len(ln) else '#'
            if left == '.' and right == '.':
                score += WEIGHTS["OPEN_TWO"]
            else:
                score += WEIGHTS["DEAD_TWO"]
        return score

    return _count(p_line), _count(o_line)