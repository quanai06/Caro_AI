def check_win(board, last_row, last_col, player):
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for dr, dc in directions:
        count = 1
        # forward
        for step in range(1, 6):   # từ 1 đến 5
            r, c = last_row + dr*step, last_col + dc*step
            if not (0 <= r < board.size and 0 <= c < board.size) or board.grid[r][c] != player:
                break
            count += 1
        # backward
        for step in range(1, 6):   # từ 1 đến 5
            r, c = last_row - dr*step, last_col - dc*step
            if not (0 <= r < board.size and 0 <= c < board.size) or board.grid[r][c] != player:
                break
            count += 1
        if count >= 5:              
            return True
    return False