import timeit
import logging
import pygame as p
from Chess import ChessEngine
from Chess import ChessAI


WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT / DIMENSION
MAX_FPS = 15
IMAGES = {}
LIGHT_SQ_COLOR = 'burlywood1'
DARK_SQ_COLOR = 'burlywood3'
LIGHT_SQ_MOVED_COLOR = 'lightgoldenrod1'
DARK_SQ_MOVED_COLOR = 'lightgoldenrod3'
LIGHT_SQ_SELECTED_COLOR = 'chocolate1'
DARK_SQ_SELECTED_COLOR = 'chocolate3'
POSSIBLE_MOVE_COLOR = 'palegreen4'
STALEMATE_COLOR = 'lightslateblue'
CHECKMATE_LOSE_COLOR = 'indianred2'  # 'lightcoral'
CHECKMATE_WIN_COLOR = 'mediumseagreen'  # 'chartreuse3' 'lightgreen'
IS_HUMAN = (False, True)  # (White, Black)


def load_images():
    pieces = ['bP', 'bR', 'bN', 'bB', 'bQ', 'bK', 'wP', 'wR', 'wN', 'wB', 'wQ', 'wK']
    for piece in pieces:
        IMAGES[piece] = p.image.load("images/" + piece + ".png")


def main():
    logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.DEBUG)
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    load_images()
    gs = ChessEngine.GameState()

    running = True
    is_human_player = (IS_HUMAN[0], IS_HUMAN[1])
    white_ai = ChessAI.AIState() if not IS_HUMAN[0] else None
    black_ai = ChessAI.AIState() if not IS_HUMAN[1] else None
    game_over = False
    valid_moves = gs.get_valid_moves()
    move_made = False
    sq_selected = ()
    player_clicks = []
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_over = False
                    gs.isStaleMate = False
                    gs.isCheckMate = False
                    gs.undo_move()
                    move_made = True
                    sq_selected = ()
                    player_clicks = []

            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and is_human_player[1 - gs.whiteToMove]:
                    location = p.mouse.get_pos()
                    col = int(location[0]//SQ_SIZE)
                    row = int(location[1]//SQ_SIZE)
                    if sq_selected == (row, col):  # deselect if click on the same piece
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        if gs.selectedSquare != ():  # 2nd click on diff piece but same color => 2nd click as new 1st click
                            if gs.board[gs.selectedSquare[0]][gs.selectedSquare[1]][0] == gs.board[row][col][0]:
                                player_clicks = []
                        else:  # first click, has to be on a piece of the turn's color
                            if (gs.whiteToMove and gs.board[row][col][0] != "w") or \
                                    (not gs.whiteToMove and gs.board[row][col][0] != "b"):
                                sq_selected = ()
                                player_clicks = []

                    if sq_selected != ():
                        player_clicks.append(sq_selected)

                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        if move in valid_moves:
                            for a_valid_move in valid_moves:
                                if move == a_valid_move:
                                    move = a_valid_move  # because 'a_valid_move' has more properties than 'move'.
                            gs.make_move(move, valid_moves)
                            move_made = True
                            sq_selected = ()
                            player_clicks = []
                        else:
                            print("Not a valid move")
                            player_clicks.pop()
                            sq_selected = gs.selectedSquare

        if not move_made and not game_over and not is_human_player[1 - gs.whiteToMove]:
            start_time = timeit.default_timer()
            current_turn_ai = white_ai if gs.whiteToMove else black_ai

            total_possible_moves = current_turn_ai.count_all_moves_at_depth(gs, current_turn_ai.depth)
            print(f'total possible moves : {total_possible_moves}')

            current_turn_ai.start_search(gs)
            ai_move = current_turn_ai.chosen_move
            print(f"Time: {timeit.default_timer() - start_time}")
            logging.debug(gs.get_fen_from_board())
            logging.debug(f'has considered en passant : {current_turn_ai.hasConsideredEnPassant}')
            gs.make_move(ai_move, valid_moves)
            move_made = True

        if move_made:
            move_made = False
            valid_moves = gs.get_valid_moves()
            game_over = gs.isCheckMate or gs.isStaleMate
            if len(gs.notationMoveLog) > 0:
                logging.debug(gs.notationMoveLog[-1])
                logging.debug(f'castling rights : {gs.castlingRightsLog[-1]}')
                logging.debug(f'kings position : {gs.kingPosition}')
            if game_over:
                moves_notation = gs.get_moves_notation_from_log()
                print(f"{moves_notation}")
                is_human_player = (True, True)
            logging.debug(gs.get_fen_from_board())

        gs.selectedSquare = sq_selected
        draw_game_state(screen, gs, valid_moves)

        clock.tick(MAX_FPS)
        p.display.flip()


def draw_game_state(screen, gs, valid_moves):
    draw_board(screen)
    draw_highlighted_squares(screen, gs, valid_moves)
    draw_piece(screen, gs.board)


def draw_board(screen):
    colors = [p.Color(LIGHT_SQ_COLOR), p.Color(DARK_SQ_COLOR)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r+c) % 2]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_highlighted_squares(screen, gs, valid_moves):
    # Previous move highlighting
    if len(gs.moveLog) != 0:
        colors_moved = [p.Color(LIGHT_SQ_MOVED_COLOR), p.Color(DARK_SQ_MOVED_COLOR)]
        last_move = gs.moveLog[-1]
        start_row = last_move.startRow
        start_col = last_move.startCol
        end_row = last_move.endRow
        end_col = last_move.endCol
        p.draw.rect(screen, colors_moved[(start_row+start_col) % 2],
                    p.Rect(start_col * SQ_SIZE, start_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.draw.rect(screen, colors_moved[(end_row+end_col) % 2],
                    p.Rect(end_col * SQ_SIZE, end_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    # Possible move highlighting
    if gs.selectedSquare != ():
        colors_selected = [p.Color(LIGHT_SQ_SELECTED_COLOR), p.Color(DARK_SQ_SELECTED_COLOR)]
        selected_row = gs.selectedSquare[0]
        selected_col = gs.selectedSquare[1]
        p.draw.rect(screen, colors_selected[(selected_row + selected_col) % 2],
                    p.Rect(selected_col * SQ_SIZE, selected_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        for move in valid_moves:
            if move.startRow == selected_row and move.startCol == selected_col:
                possible_row = move.endRow
                possible_col = move.endCol
                if move.pieceCaptured == "--":
                    p.draw.circle(screen, POSSIBLE_MOVE_COLOR,
                                  (possible_col * SQ_SIZE + SQ_SIZE/2, possible_row * SQ_SIZE + SQ_SIZE/2), SQ_SIZE/10)
                else:
                    for c in range(2):
                        for r in range(2):
                            p.draw.polygon(screen, POSSIBLE_MOVE_COLOR,
                                           points=[((possible_col + c) * SQ_SIZE, (possible_row + r) * SQ_SIZE),
                                                   ((possible_col + c) * SQ_SIZE + (1 - 2 * c) * SQ_SIZE / 5, (possible_row + r) * SQ_SIZE),
                                                   ((possible_col + c) * SQ_SIZE, (possible_row + r) * SQ_SIZE + (1 - 2 * r) * SQ_SIZE / 5)])

    # CheckMate and stalemate highlighting
    kings = gs.kingPosition
    if gs.isCheckMate:
        p.draw.rect(screen, CHECKMATE_LOSE_COLOR,
                    p.Rect(kings[1 - gs.whiteToMove][1] * SQ_SIZE, kings[1 - gs.whiteToMove][0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.draw.rect(screen, CHECKMATE_WIN_COLOR,
                    p.Rect(kings[gs.whiteToMove][1] * SQ_SIZE, kings[gs.whiteToMove][0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))
    if gs.isStaleMate:
        p.draw.rect(screen, STALEMATE_COLOR,
                    p.Rect(kings[1 - gs.whiteToMove][1] * SQ_SIZE, kings[1 - gs.whiteToMove][0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.draw.rect(screen, STALEMATE_COLOR,
                    p.Rect(kings[gs.whiteToMove][1] * SQ_SIZE, kings[gs.whiteToMove][0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_piece(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


if __name__ == "__main__":
    main()
