from ..game.rules import check_win

WIN_VALUE = 10_000_000
BLOCK_VALUE = 0


def opponent_of(player):
    return 'X' if player == 'O' else 'O'


def move_wins(board, move, player):
    test_board = board.clone()
    test_board.place(move[0], move[1], player)
    return check_win(test_board, move[0], move[1], player)


def find_forced_move(board, moves, player):
    """
    Chọn nước bắt buộc ở root theo cùng luật cho Minimax và Alpha-Beta:
    - Nếu player có thể thắng ngay, đi thắng luôn.
    - Nếu đối thủ có thể thắng ngay, chặn ngay.
    """
    opponent = opponent_of(player)

    for move in moves:
        if move_wins(board, move, player):
            return move, WIN_VALUE

    for move in moves:
        if move_wins(board, move, opponent):
            return move, BLOCK_VALUE

    return None, None


def order_moves_advanced(board, moves, player, depth):
    """
    Sắp xếp nước đi theo heuristic:
    - Nước tạo chiến thắng ngay: ưu tiên cao nhất
    - Nước chặn đối thủ (kiểm tra nếu đối thủ đặt vào đó sẽ thắng): ưu tiên cao
    - Nước gần tâm
    - Dùng evaluate sơ bộ (nhanh) để ước lượng
    """
    scored = []
    center = board.size // 2
    opponent = opponent_of(player)

    for move in moves:
        # 1. Nếu nước này thắng ngay cho player
        test_board = board.clone()
        test_board.place(move[0], move[1], player)
        if check_win(test_board, move[0], move[1], player):
            priority = 1_000_000
        # 2. Nếu nước này chặn đối thủ thắng (đối thủ đặt vào đó sẽ thắng)
        elif move_wins(board, move, opponent):
            priority = 500_000
        else:
            # 3. Heuristic đơn giản: điểm từ evaluate nhanh + khoảng cách tâm
            # Dùng hàm _score_cell từ evaluation (nếu có) hoặc đánh giá nhanh
            try:
                from .evaluation import _score_cell
                score = _score_cell(test_board, move[0], move[1], player)
            except:
                # Fallback: đếm số lượng quân lân cận
                score = 0
                for dr, dc in [(1,0),(0,1),(1,1),(1,-1)]:
                    cnt = 1
                    for step in range(1, 3):
                        r, c = move[0] + dr*step, move[1] + dc*step
                        if 0 <= r < board.size and 0 <= c < board.size and board.grid[r][c] == player:
                            cnt += 1
                        else:
                            break
                    for step in range(1, 3):
                        r, c = move[0] - dr*step, move[1] - dc*step
                        if 0 <= r < board.size and 0 <= c < board.size and board.grid[r][c] == player:
                            cnt += 1
                        else:
                            break
                    score += cnt * cnt
            # Khoảng cách đến tâm (càng gần càng tốt)
            dist = abs(move[0] - center) + abs(move[1] - center)
            priority = score - dist * 10
        scored.append((priority, move))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [move for _, move in scored]
