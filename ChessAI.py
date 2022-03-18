import random

INFINITY = 200000
CHECKMATE = 100000
STALEMATE = 0
DEPTH = 2
MC_PATHS = 1000
END_OF_OPENING_PHASE_MOVES = 20
PIECES_ON_BOARD_FOR_END_GAME = 10
BASE_VALUES = {'P': 100, 'N': 280, 'B': 320, 'R': 500, 'Q': 900, 'K': 300, '-': 0}
BUMP_VALUES = {
    'P': [[0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 5, 10, 15, 15, 10, 5, 0],
          [0, 0, 5, 15, 15, 5, 0, 0],
          [0, 0, 5, 10, 10, 5, 0, 0],
          [0, 0, 5, 5, 5, 5, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0]],
    'N': [[-60, -40, -30, -30, -30, -30, -40, -60],
          [-40, -20, 0, 0, 0, 0, -20, -40],
          [-25, 0, 10, 15, 15, 10, 0, -25],
          [-20, 5, 15, 25, 25, 15, 5, -20],
          [-20, 0, 15, 25, 25, 15, 0, -20],
          [-25, 5, 10, 15, 15, 10, 5, -25],
          [-40, -20, 0, 10, 10, 0, -20, -40],
          [-60, -40, -30, -30, -30, -30, -40, -60]],
    'B': [[-20, -10, -10, -10, -10, -10, -10, -20],
          [-10, 0, 0, 0, 0, 0, 0, -10],
          [-10, 0, 5, 15, 15, 5, 0, -10],
          [-10, 5, 10, 20, 20, 10, 5, -10],
          [-10, 0, 15, 20, 20, 15, 0, -10],
          [-10, 10, 10, 15, 15, 10, 10, -10],
          [-10, 10, 0, 0, 0, 0, 10, -10],
          [-20, -10, -10, -10, -10, -10, -10, -20]],
    'R': [[5, 10, 10, 10, 10, 10, 10, 5],
          [10, 15, 20, 20, 20, 20, 15, 10],
          [5, 10, 10, 15, 15, 10, 10, 5],
          [0, 0, 5, 5, 5, 5, 0, 0],
          [0, 0, 5, 5, 5, 5, 0, 0],
          [0, 0, 5, 5, 5, 5, 0, 0],
          [0, 0, 5, 5, 5, 5, 0, 0],
          [0, 0, 5, 10, 10, 5, 0, 0]],
    'Q': [[0, 0, 0, 0, 0, 0, 0, 0],
          [0, 5, 5, 5, 5, 5, 5, 0],
          [0, 5, 10, 10, 10, 10, 5, 0],
          [0, 5, 10, 20, 20, 10, 5, 0],
          [0, 5, 10, 20, 20, 10, 5, 0],
          [0, 5, 10, 10, 10, 10, 5, 0],
          [0, 5, 5, 5, 5, 5, 5, 0],
          [0, 0, 0, 0, 0, 0, 0, 0]],
    'K': [[0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [5, 20, 10, 0, 0, 0, 20, 5]],
    '-': [[0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0]],
}


class AIState:
    def __init__(self):
        self.best_moves = []
        self.best_scores = []
        self.nodes_count = 0
        self.chosen_move = None
        self.chosen_score = 0
        self.depth = DEPTH
        self.hasConsideredEnPassant = False  # for debug

    def start_search(self, game_state):
        self.hasConsideredEnPassant = False  # for debug
        self.nodes_count = 0
        best_score = self.negamax_pruning_move(game_state, self.depth, -INFINITY, INFINITY)
        direction = 1 if game_state.whiteToMove else -1
        print(f"{self.nodes_count} nodes computed")
        return best_score * direction

    def negamax_pruning_move(self, game_state, depth, alpha, beta):
        if depth == 0:
            return self.quiescence_move(game_state, alpha, beta)
        else:
            valid_moves = game_state.get_valid_moves()
            valid_moves = self.order_by_candidate_moves(valid_moves, depth)
            if game_state.isCheckMate or game_state.isStaleMate:
                return self.quiescence_move(game_state, alpha, beta)

            direction = 1 if game_state.whiteToMove else -1
            best_score = -INFINITY

            for move in valid_moves:
                game_state.make_move(move)
                self.hasConsideredEnPassant = self.hasConsideredEnPassant or move.isEnPassant  # for debug
                new_score = -1 * self.negamax_pruning_move(game_state, depth - 1, -beta, -alpha)
                game_state.undo_move()
                self.nodes_count += 1

                if new_score > best_score:
                    best_score = new_score

                    if depth == self.depth:
                        self.best_moves.insert(0, move)
                        self.best_scores.insert(0, best_score)
                        self.chosen_move = move
                        self.chosen_score = best_score
                        print(f"{self.chosen_move.get_chess_notation()}, {best_score * direction}")

                if best_score > alpha:
                    alpha = best_score
                if alpha >= beta:
                    break

            return best_score

    def quiescence_move(self, game_state, alpha, beta):
        direction = 1 if game_state.whiteToMove else -1
        base_score = self.score_board(game_state.board, direction)
        if base_score > alpha:
            alpha = base_score
        if alpha > beta:
            return beta

        # if this move was not a capture exit, otherwise test the opponent captures
        last_move = game_state.moveLog[-1]
        if last_move.pieceCaptured == '--':
            return base_score

        # get the opponent capture responses
        valid_moves = game_state.get_valid_moves()
        valid_moves = game_state.get_capture_moves(valid_moves)

        for move in valid_moves:
            game_state.make_move(move)
            self.hasConsideredEnPassant = self.hasConsideredEnPassant or move.isEnPassant  # for debug
            new_score = -1 * self.quiescence_move(game_state, -beta, -alpha)
            game_state.undo_move()
            self.nodes_count += 1

            if new_score > alpha:
                alpha = new_score
            if new_score >= beta:
                return beta

        return alpha

    @staticmethod
    def score_board(board, direction):
        score = 0
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col][0] == 'w':
                    multiplier = 1
                    bump_row = row
                    bump_col = col
                else:
                    multiplier = -1
                    bump_row = 7 - row
                    bump_col = col
                bump = BUMP_VALUES[board[row][col][1]][bump_row][bump_col]
                score += (BASE_VALUES[board[row][col][1]] + bump) * multiplier

        return score * direction

    @staticmethod
    def game_phase_index(game_state, board):  # returns 0 for open, 1 for mid, 2 for late
        moves_played = len(game_state.moveLog)
        if moves_played <= END_OF_OPENING_PHASE_MOVES:
            return 0
        if sum([piece != "--" for piece in board]) <= PIECES_ON_BOARD_FOR_END_GAME:
            return 2
        return 1

    def order_by_candidate_moves(self, moves, depth):
        random.shuffle(moves)

        if depth == self.depth and len(self.best_moves) > 0:
            # intersect_moves
            moves_id = {move.moveID for move in moves}
            ai_state_moves_id = {move.moveID for move in self.best_moves}
            intersect_moves_id = list(moves_id.intersection(ai_state_moves_id))
            intersect_moves = [move for move in self.best_moves if move.moveID in intersect_moves_id]
            other_moves = [move for move in moves if move.moveID not in intersect_moves_id]
            capture_moves = [move for move in other_moves if move.pieceCaptured != "--"]
            other_moves = [move for move in other_moves if move.pieceCaptured == "--"]
            intersect_moves.extend(capture_moves)
            intersect_moves.extend(other_moves)
            return intersect_moves

        return moves

    def find_best_move(self, game_state):
        direction = 1 if game_state.whiteToMove else -1
        best_score = -direction * INFINITY
        best_move = None
        valid_moves = game_state.get_valid_moves()

        if game_state.isCheckMate:
            return best_move, -direction * CHECKMATE
        if game_state.isStaleMate:
            return best_move, -direction * STALEMATE

        random.shuffle(valid_moves)

        for move in valid_moves:
            game_state.make_move(move)
            score = self.score_board(game_state.board, direction)
            game_state.undo_move()
            if score * direction > best_score * direction:
                best_score = score
                best_move = move

        return best_move, best_score

    @staticmethod
    def find_random_move(valid_moves):
        z = random.randint(0, len(valid_moves) - 1)
        return valid_moves[z]

    def count_all_moves_at_depth(self, game_state, depth):
        if depth == 0:
            return 1

        num_positions = 0
        valid_moves = game_state.get_valid_moves()
        for move in valid_moves:
            game_state.make_move(move)
            num_positions += self.count_all_moves_at_depth(game_state, depth - 1)
            game_state.undo_move()

        return num_positions

