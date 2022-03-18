MOVES_TILL_STALEMATE = 75


class GameState:
    PiecesToFEN = {'bP': 'p', 'bR': 'r', 'bN': 'n', 'bB': 'b', 'bQ': 'q', 'bK': 'k',
                   'wP': 'P', 'wR': 'R', 'wN': 'N', 'wB': 'B', 'wQ': 'Q', 'wK': 'K'}
    FENToPieces = {v: k for k, v in PiecesToFEN.items()}

    def __init__(self):
        self.moveFunctions = {'P': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                              'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}

        self.FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.FEN = "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"
        self.board, self.kingPosition, self.whiteToMove, self.canOO, self.canOOO, \
            self.enPassantTarget, self.moveRuleCount = self.get_board_from_fen(self.FEN)
        self.Zobrist: int = 0
        self.moveLog = []
        self.notationMoveLog = []
        self.moveRuleLog = [int(self.moveRuleCount)]
        self.castlingRightsLog = [((self.canOO[0], self.canOO[1]), (self.canOOO[0], self.canOOO[1]))]  # initialize the castling rights log

        self.selectedSquare = ()
        self.pinnedPieces = []
        self.checkingPieces = []
        self.isCheckAfterOpponentMove = False
        self.isCheck = False
        self.isCheckMate = False
        self.isStaleMate = False

    def make_move(self, move, valid_moves=None):
        self.board[move.startRow][move.startCol] = '--'
        self.board[move.endRow][move.endCol] = move.pieceMoved

        en_passant = move.isEnPassant
        promoting = move.isPromotion
        castling_oo = move.isCastling_OO
        castling_ooo = move.isCastling_OOO
        if promoting:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + "Q"
        if en_passant:
            self.board[move.startRow][move.endCol] = '--'
        if castling_oo:
            self.board[move.endRow][move.endCol + 1] = '--'
            self.board[move.endRow][move.endCol - 1] = move.pieceMoved[0] + "R"
        if castling_ooo:
            self.board[move.endRow][move.endCol - 2] = '--'
            self.board[move.endRow][move.endCol + 1] = move.pieceMoved[0] + "R"

        if move.pieceMoved[1] == "K":
            self.kingPosition[1 - self.whiteToMove] = (move.endRow, move.endCol)

        self.update_castling_rights(move)

        if move.pieceCaptured == "--" and move.pieceMoved[1] != "P":  # not a capture nor a pawn move
            moves_count = int(self.moveRuleLog[-1])
            self.moveRuleLog.append(moves_count + 1)
            self.moveRuleCount = moves_count + 1
        else:
            self.moveRuleLog.append(0)
            self.moveRuleCount = 0

        self.whiteToMove = not self.whiteToMove

        # add move to move log
        self.moveLog.append(move)

        # add move to notation move log
        move_from_prefix = ""
        if valid_moves:
            for a_valid_move in valid_moves:
                if move != a_valid_move:
                    if a_valid_move.endRow == move.endRow and a_valid_move.endCol == move.endCol and \
                            a_valid_move.pieceMoved == move.pieceMoved:
                        move_from_prefix = "r_" + str(move.startRow) if move.startCol == a_valid_move.startCol else "c_" + str(move.startCol)
        notation_move = move.get_chess_notation(move_from_prefix)
        self.notationMoveLog.append(notation_move)

    def undo_move(self):
        if len(self.moveLog) != 0:
            self.isCheckMate = False
            self.isStaleMate = False
            self.notationMoveLog.pop()
            self.moveRuleLog.pop()
            self.moveRuleCount = int(self.moveRuleLog[-1])
            move = self.moveLog.pop()
            if len(self.notationMoveLog) != 0:
                self.isCheck = (self.notationMoveLog[-1][-1] == "+")
            self.whiteToMove = not self.whiteToMove

            self.undo_update_castling_rights()

            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.board[move.startRow][move.startCol] = move.pieceMoved

            en_passant = move.isEnPassant
            castling_oo = move.isCastling_OO
            castling_ooo = move.isCastling_OOO
            if en_passant:
                self.board[move.endRow][move.endCol] = '--'
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            if castling_oo:
                self.board[move.endRow][move.endCol - 1] = '--'
                self.board[move.endRow][move.endCol + 1] = move.pieceMoved[0] + "R"
            if castling_ooo:
                self.board[move.endRow][move.endCol + 1] = '--'
                self.board[move.endRow][move.endCol - 2] = move.pieceMoved[0] + "R"

            if move.pieceMoved[1] == "K":
                self.kingPosition[1 - self.whiteToMove] = (move.startRow, move.startCol)

    def update_castling_rights(self, move):
        if move.pieceMoved[1] == "K":  # update own castling rights
            self.canOO[1 - self.whiteToMove] = False
            self.canOOO[1 - self.whiteToMove] = False
        elif move.pieceMoved[1] == "R":  # update own castling rights
            if move.startCol == 7:
                self.canOO[1 - self.whiteToMove] = False
            elif move.startCol == 0:
                self.canOOO[1 - self.whiteToMove] = False
        elif move.pieceCaptured[1] == "R":  # update opponent castling rights
            if move.endCol == 7 and self.canOO[self.whiteToMove]:
                self.canOO[self.whiteToMove] = False
            elif move.endCol == 0 and self.canOOO[self.whiteToMove]:
                self.canOOO[self.whiteToMove] = False

        castle_oo = (self.canOO[0], self.canOO[1])
        castle_ooo = (self.canOOO[0], self.canOOO[1])

        self.castlingRightsLog.append((castle_oo, castle_ooo))

    def undo_update_castling_rights(self):
        self.castlingRightsLog.pop()
        castle_rights = self.castlingRightsLog[-1]
        self.canOO = [castle_rights[0][0], castle_rights[0][1]]
        self.canOOO = [castle_rights[1][0], castle_rights[1][1]]

    def get_pinned_and_checking_pieces(self):
        pinned_pieces = []
        checking_pieces = []
        if self.whiteToMove:
            king_position = self.kingPosition[0]
            opposite_color = "b"
            ally_color = "w"
            sign_direction = -1
        else:
            king_position = self.kingPosition[1]
            opposite_color = "w"
            ally_color = "b"
            sign_direction = 1

        list_directions = [[(-1, 0), (0, 1), (1, 0), (0, -1)], [(-1, 1), (1, 1), (1, -1), (-1, -1)]]
        list_attacking_pieces = [["R", "Q"], ["B", "Q"]]
        for directions in list_directions:
            attacking_pieces = list_attacking_pieces[list_directions.index(directions)]
            for direction in directions:
                count_ally_pieces = 0
                possible_pinned_piece = ()
                for i in range(1, 8):
                    new_row = king_position[0] + direction[0] * i
                    new_col = king_position[1] + direction[1] * i
                    if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                        new_piece = self.board[new_row][new_col]
                        if new_piece[0] == opposite_color:
                            if new_piece[1] in attacking_pieces:
                                if count_ally_pieces == 1:
                                    pinned_pieces.append(possible_pinned_piece)
                                    break
                                else:
                                    checking_pieces.append((new_row, new_col, new_piece[1], direction[0], direction[1]))
                            else:
                                break
                        elif new_piece[0] == ally_color:
                            count_ally_pieces = count_ally_pieces + 1
                            if count_ally_pieces == 1:
                                possible_pinned_piece = (new_row, new_col, new_piece[1], direction[0], direction[1])
                            else:
                                break
                    else:
                        break

        # Separate process for Knights & King (only for checks)
        list_directions = [[(-2, 1), (-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1)],
                           [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]]
        list_attacking_pieces = ["N", "K"]
        for directions in list_directions:
            attacking_piece = list_attacking_pieces[list_directions.index(directions)]
            for direction in directions:
                new_row = king_position[0] + direction[0]
                new_col = king_position[1] + direction[1]
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    new_piece = self.board[new_row][new_col]
                    if new_piece[0] == opposite_color and new_piece[1] == attacking_piece:
                        checking_pieces.append((new_row, new_col, new_piece[1], direction[0], direction[1]))

        # Separate process for Pawns (only for checks)
        directions = [-1, 1]
        for direction in directions:
            new_row = king_position[0] + sign_direction
            new_col = king_position[1] + direction
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                new_piece = self.board[new_row][new_col]
                if new_piece == opposite_color + 'P':
                    checking_pieces.append((new_row, new_col, new_piece[1], sign_direction, direction))

        is_in_check = False
        if len(checking_pieces) > 0:
            is_in_check = True

        return pinned_pieces, checking_pieces, is_in_check

    def is_move_valid(self, move):
        piece_to_move = move.pieceMoved
        row_from = move.startRow
        col_from = move.startCol
        row_to = move.endRow
        col_to = move.endCol
        king_row = self.kingPosition[1 - self.whiteToMove][0]
        king_col = self.kingPosition[1 - self.whiteToMove][1]
        if self.whiteToMove:
            opposite_color = "b"
        else:
            opposite_color = "w"

        is_valid = False
        if piece_to_move[1] == "K" or move.isEnPassant:
            potential_move = Move((row_from, col_from), (row_to, col_to), self.board, move.isPromotion, move.isEnPassant)
            self.make_move(potential_move)
            self.whiteToMove = not self.whiteToMove
            unused_pins, unused_check, potential_check = self.get_pinned_and_checking_pieces()
            if not potential_check:
                is_valid = True
            self.whiteToMove = not self.whiteToMove
            self.undo_move()
        else:
            if len(self.checkingPieces) > 1:  # Double check, only K can move
                is_valid = False
            elif len(self.checkingPieces) == 1:  # Single check, piece can try to eat or block
                if self.checkingPieces[0][2] == "N":  # Can only try to eat
                    if row_to == self.checkingPieces[0][0] and col_to == self.checkingPieces[0][1]:
                        is_valid = True
                else:
                    max_i = max(abs((self.checkingPieces[0][0] - king_row) * self.checkingPieces[0][3]),
                                abs((self.checkingPieces[0][1] - king_col) * self.checkingPieces[0][4]))
                    for i in range(1, max_i + 1):
                        if row_to == king_row + i * self.checkingPieces[0][3] and col_to == king_col + i * self.checkingPieces[0][4]:
                            is_valid = True
                            break
            else:  # No check, but see if piece is pinned
                is_valid = True
                for i in range(len(self.pinnedPieces)):
                    if row_from == self.pinnedPieces[i][0] and col_from == self.pinnedPieces[i][1]:
                        is_valid = False
                        max_j = 0
                        for j in range(1, 8):
                            if self.board[king_row + j * self.pinnedPieces[i][3]][king_col + j * self.pinnedPieces[i][4]][0] == opposite_color:
                                max_j = j
                                break
                        for j in range(1, max_j + 1):
                            if row_to == king_row + j * self.pinnedPieces[i][3] and col_to == king_col + j * self.pinnedPieces[i][4]:
                                is_valid = True
                                break

        return is_valid

    def get_valid_moves(self):
        self.pinnedPieces, self.checkingPieces, self.isCheck = self.get_pinned_and_checking_pieces()
        '''
        if self.isCheck:
            print(f"{'White' if self.whiteToMove else 'Black'} King is in check")
        if len(self.pinnedPieces) != 0:
            print(f"Pinned pieces {*self.pinnedPieces,}")
        if len(self.checkingPieces) != 0:
            print(f"Checking pieces {*self.checkingPieces,}")
        '''

        possible_moves = self.get_all_possible_moves()
        # print(f"{len(possible_moves)} possible moves")

        valid_moves = []
        for move in possible_moves:
            is_valid = self.is_move_valid(move)
            if is_valid:
                valid_moves.append(move)
        # print(f"{len(valid_moves)} valid moves")

        if not valid_moves:
            if self.isCheck:
                self.isCheckMate = True
                self.notationMoveLog[-1] = self.notationMoveLog[-1] + "#"
            else:
                self.isStaleMate = True
        else:
            if self.isCheck:
                self.notationMoveLog[-1] = self.notationMoveLog[-1] + "+"
            if self.moveRuleLog[-1] == MOVES_TILL_STALEMATE:
                self.isStaleMate = True

        return valid_moves

    def get_all_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    moves = moves + self.moveFunctions[piece](r, c)
        return moves

    def get_pawn_moves(self, r, c):
        moves = []
        if self.whiteToMove:
            opposite_color = "b"
            sign_direction = -1
            pawn_starting_row = 6
        else:
            opposite_color = "w"
            sign_direction = 1
            pawn_starting_row = 1

        # check if the potential move will get to a promotion
        got_to_backend_row = (r + 1 * sign_direction == pawn_starting_row + 6 * sign_direction)

        if self.board[r + 1 * sign_direction][c] == "--":  # Move up
            moves.append(Move((r, c), (r + 1 * sign_direction, c), self.board, got_to_backend_row))
            if r == pawn_starting_row and self.board[r + 2 * sign_direction][c] == "--":
                moves.append(Move((r, c), (r + 2 * sign_direction, c), self.board))
        if c - 1 >= 0:  # Capture on one side
            if self.board[r + 1 * sign_direction][c - 1][0] == opposite_color:
                moves.append(Move((r, c), (r + 1 * sign_direction, c - 1), self.board, got_to_backend_row))
        if c + 1 <= 7:  # Capture on the other side
            if self.board[r + 1 * sign_direction][c + 1][0] == opposite_color:
                moves.append(Move((r, c), (r + 1 * sign_direction, c + 1), self.board, got_to_backend_row))

        # Add potential en passant moves
        if len(self.moveLog) > 0:
            last_move: Move = self.moveLog[-1]
            piece_moved = last_move.pieceMoved
            piece_moved_row = last_move.endRow
            piece_moved_col = last_move.endCol
            piece_from_row = last_move.startRow
            if piece_moved[1] == "P":
                if abs(piece_moved_col - c) == 1 and abs(piece_moved_row - piece_from_row) == 2:
                    if r == pawn_starting_row + 3 * sign_direction:
                        moves.append(Move((r, c), (r + 1 * sign_direction, piece_moved_col), self.board, False, True))
                        # self.enPassantTarget = (r + 1 * sign_direction, piece_moved_col)

        return moves

    def get_rook_moves(self, r, c):
        moves = []
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        opposite_color = "w"
        if self.whiteToMove:
            opposite_color = "b"

        for direction in directions:
            for i in range(1, 8):
                new_row = r + direction[0] * i
                new_col = c + direction[1] * i
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    if self.board[new_row][new_col] == "--":
                        moves.append(Move((r, c), (new_row, new_col), self.board))
                    elif self.board[new_row][new_col][0] == opposite_color:
                        moves.append(Move((r, c), (new_row, new_col), self.board))
                        break
                    else:
                        break

        return moves

    def get_knight_moves(self, r, c):
        moves = []
        directions = [(-2, 1), (-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1)]
        own_color = "b"
        if self.whiteToMove:
            own_color = "w"

        for direction in directions:
            if 0 <= r + direction[0] <= 7 and 0 <= c + direction[1] <= 7:
                if self.board[r + direction[0]][c + direction[1]][0] != own_color:
                    moves.append(Move((r, c), (r + direction[0], c + direction[1]), self.board))

        return moves

    def get_bishop_moves(self, r, c):
        moves = []
        directions = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
        opposite_color = "w"
        if self.whiteToMove:
            opposite_color = "b"

        for direction in directions:
            for i in range(1, 8):
                new_row = r + direction[0] * i
                new_col = c + direction[1] * i
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    if self.board[new_row][new_col] == "--":
                        moves.append(Move((r, c), (new_row, new_col), self.board))
                    elif self.board[new_row][new_col][0] == opposite_color:
                        moves.append(Move((r, c), (new_row, new_col), self.board))
                        break
                    else:
                        break

        return moves

    def get_queen_moves(self, r, c):
        moves = []
        moves = moves + self.get_rook_moves(r, c)
        moves = moves + self.get_bishop_moves(r, c)
        return moves

    def get_king_moves(self, r, c):
        moves = []
        directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
        if self.whiteToMove:
            own_color = "w"
            is_oo_possible = self.canOO[0]
            is_ooo_possible = self.canOOO[0]
        else:
            own_color = "b"
            is_oo_possible = self.canOO[1]
            is_ooo_possible = self.canOOO[1]

        for direction in directions:
            if 0 <= r + direction[0] <= 7 and 0 <= c + direction[1] <= 7:
                if self.board[r + direction[0]][c + direction[1]][0] != own_color:
                    moves.append(Move((r, c), (r + direction[0], c + direction[1]), self.board))

        # Add potential castling
        if is_oo_possible:
            if all(self.board[r][c_step] == "--" for c_step in range(c + 1, 7)):
                if all(self.is_move_valid(Move((r, c), (r, c_step), self.board)) for c_step in range(c, 7)):
                    moves.append(Move((r, c), (r, c + 2), self.board, False, False, (True, False)))
                    # print("Castle King side possible")

        if is_ooo_possible:
            if all(self.board[r][c_step] == "--" for c_step in range(2, c)):
                if all(self.is_move_valid(Move((r, c), (r, c_step), self.board)) for c_step in range(2, c + 1)):
                    moves.append(Move((r, c), (r, c - 2), self.board, False, False, (False, True)))
                    # print("Castle Queen side possible")

        return moves

    def is_en_passant_move(self, move):
        piece_moved = move.pieceMoved
        piece_captured = move.pieceCaptured
        piece_moved_row = move.endRow
        piece_moved_col = move.endCol
        piece_from_col = move.startCol

        if self.whiteToMove:
            en_passant_row = 2
        else:
            en_passant_row = 6

        if piece_moved[1] == "P" and piece_captured == "--":
            if en_passant_row == piece_moved_row and abs(piece_moved_col - piece_from_col) == 1:
                return True

        return False

    def is_pawn_promotion(self, move):
        piece_moved = move.pieceMoved
        piece_moved_row = move.endRow

        if self.whiteToMove:
            promotion_row = 0
        else:
            promotion_row = 7

        if piece_moved[1] == "P":
            if promotion_row == piece_moved_row:
                return True

        return False

    def get_board_from_fen(self, fen_string):
        fen_split = fen_string.split()

        # First part of the FEN
        board = [[]]
        row = 0
        col = 0
        w_king_pos = (7, 4)
        b_king_pos = (0, 4)
        for char in fen_split[0]:
            if char == '/':
                board.append([])
                row += 1
                col = 0
            elif char.isnumeric():
                spaces = int(char)
                for i in range(spaces):
                    board[row].append('--')
                    col += 1
            else:
                board[row].append(self.FENToPieces[char])
                if char == 'k':
                    b_king_pos = (row, col)
                elif char == 'K':
                    w_king_pos = (row, col)
                col += 1
        king_position = [w_king_pos, b_king_pos]

        # 2nd part of the FEN
        white_to_move = (fen_split[1] == 'w')

        # 3rd part of the FEN
        can_oo = ['K' in fen_split[2], 'k' in fen_split[2]]
        can_ooo = ['Q' in fen_split[2], 'q' in fen_split[2]]

        # 4th part of the FEN
        en_passant_target = fen_split[3]

        # 5th part of the FEN
        move_rule_count = fen_split[4]

        return board, king_position, white_to_move, can_oo, can_ooo, en_passant_target, move_rule_count

    def get_fen_from_board(self):
        # First part of the FEN
        fen_board = ''
        count_blanks = 0
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                if self.board[row][col] == '--':
                    count_blanks += 1
                else:
                    fen_board += (str(count_blanks) if count_blanks > 0 else '') + self.PiecesToFEN[self.board[row][col]]
                    count_blanks = 0
            fen_board += (str(count_blanks) if count_blanks > 0 else '') + '/'
            count_blanks = 0
        fen_board = fen_board[:-1]

        # 2nd part of the FEN
        fen_turn = 'w' if self.whiteToMove else 'b'

        # 3rd part of the FEN
        fen_castling_rights = ''
        fen_castling_rights += 'K' if self.canOO[0] else ''
        fen_castling_rights += 'Q' if self.canOOO[0] else ''
        fen_castling_rights += 'k' if self.canOO[1] else ''
        fen_castling_rights += 'q' if self.canOOO[1] else ''
        fen_castling_rights = '-' if fen_castling_rights == '' else fen_castling_rights

        # 4th part of the FEN
        fen_en_passant = '-'

        # 5th part of the FEN
        fen_half_move_count = str(self.moveRuleCount)

        # 6th part of the FEN
        fen_full_moves_count = str((len(self.moveLog) + 1) // 2)

        fen_string = fen_board + ' ' + fen_turn + ' ' + fen_castling_rights + ' ' + fen_en_passant + ' ' + fen_half_move_count + ' ' + fen_full_moves_count
        # print(f"{fen_string}")
        return fen_string

    def get_moves_notation_from_log(self):
        moves_notation = ''
        move_number = 0

        for i in range(len(self.notationMoveLog)):
            notation = self.notationMoveLog[i]
            if i % 2 == 0:
                move_number += 1
                moves_notation += f"{move_number}. "
            moves_notation += f"{notation} "

        return moves_notation

    def is_king_in_check_after_opponent_move(self):
        if not self.moveLog:
            return False

        last_move: Move = self.moveLog[-1]
        piece_moved = last_move.pieceMoved
        piece_moved_row = last_move.endRow
        piece_moved_col = last_move.endCol

        if self.whiteToMove:
            sign_direction = -1
            king_position = self.kingPosition[0]
        else:
            sign_direction = 1
            king_position = self.kingPosition[1]

        match piece_moved[1]:
            case "P":
                if king_position[0] == piece_moved_row - 1 * sign_direction:
                    if abs(king_position[1] - piece_moved_col) == 1:
                        print(f"King in check by {piece_moved}")
                        return True
            case "R":
                directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                for direction in directions:
                    for i in range(1, 8):
                        new_row = piece_moved_row + direction[0] * i
                        new_col = piece_moved_col + direction[1] * i
                        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                            new_piece = self.board[new_row][new_col]
                            if new_piece != "--":
                                if new_row == king_position[0] and new_col == king_position[1]:
                                    print(f"King in check by {piece_moved}")
                                    return True
                                else:
                                    break
                        else:
                            break
            case "N":
                directions = [(-2, 1), (-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1)]
                for direction in directions:
                    if king_position[0] == piece_moved_row + direction[0] and \
                            king_position[1] == piece_moved_col + direction[1]:
                        print(f"King in check by {piece_moved}")
                        return True
            case "B":
                directions = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
                for direction in directions:
                    for i in range(1, 8):
                        new_row = piece_moved_row + direction[0] * i
                        new_col = piece_moved_col + direction[1] * i
                        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                            new_piece = self.board[new_row][new_col]
                            if new_piece != "--":
                                if new_row == king_position[0] and new_col == king_position[1]:
                                    print(f"King in check by {piece_moved}")
                                    return True
                                else:
                                    break
                        else:
                            break
            case "Q":
                directions = [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]
                for direction in directions:
                    for i in range(1, 8):
                        new_row = piece_moved_row + direction[0] * i
                        new_col = piece_moved_col + direction[1] * i
                        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                            new_piece = self.board[new_row][new_col]
                            if new_piece != "--":
                                if new_row == king_position[0] and new_col == king_position[1]:
                                    print(f"King in check by {piece_moved}")
                                    return True
                                else:
                                    break
                        else:
                            break
            case "K":
                pass  # should never happen

        return False

    def get_selected_piece_valid_moves(self):
        r = self.selectedSquare[0]
        c = self.selectedSquare[1]
        piece = self.board[r][c][1]
        possible_moves = self.moveFunctions[piece](r, c)

        valid_moves = []
        for move in possible_moves:
            is_valid = self.is_move_valid(move)
            if is_valid:
                valid_moves.append(move)

        return valid_moves

    @staticmethod
    def get_capture_moves(moves):
        moves = [move for move in moves if move.pieceCaptured != "--"]
        return moves


class Move:
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, start_square, end_square, board, is_promotion=False, is_en_passant=False, is_castling=(False, False)):
        self.startRow = start_square[0]
        self.startCol = start_square[1]
        self.endRow = end_square[0]
        self.endCol = end_square[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isEnPassant = is_en_passant
        self.isPromotion = is_promotion
        self.isCastling_OO = is_castling[0]
        self.isCastling_OOO = is_castling[1]
        self.isChecking = False
        self.isMating = False
        self.isStaleMating = False
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        if is_en_passant:
            self.pieceCaptured = board[self.startRow][self.endCol]

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def get_basic_chess_notation(self):
        return self.get_rank_file(self.startRow, self.startCol) + self.get_rank_file(self.endRow, self.endCol)

    def get_rank_file(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def get_chess_notation(self, move_from=""):
        if self.isCastling_OO:
            return "O-O"
        elif self.isCastling_OOO:
            return "O-O-O"
        else:
            captured = "x" if self.pieceCaptured != "--" else ""
            piece = self.pieceMoved[1]
            end_coordinate = self.get_basic_chess_notation()
            if piece == "P":
                piece = ""
                if captured == "x":
                    captured = end_coordinate[0] + captured
            end_coordinate = end_coordinate[2:]
            promotion_suffix = "=Q" if self.isPromotion else ""
            if move_from == "":
                move_from_suffix = ""
            else:
                if move_from[0] == "r":
                    row = int(move_from[2])
                    move_from_suffix: str = self.rowsToRanks[row]
                else:
                    col = int(move_from[2])
                    move_from_suffix: str = self.colsToFiles[col]
            return piece + move_from_suffix + captured + end_coordinate + promotion_suffix
