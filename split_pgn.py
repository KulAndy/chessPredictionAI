import re
import chess.pgn
from unidecode import unidecode
from settings import SETTINGS
import os


def clean_player_name(name):
    return unidecode(re.sub(r'[\\|/]', '_', name))


def split_pgn(pgn_file):
    splitted_dir = SETTINGS['splitted_pgns_dir']
    ignored_players = set(SETTINGS['ignored_players'])
    file_handles = {}
    game_count = 0
    max_games_before_closing = 10_000

    def get_file_handle(player, color):
        file_key = f"{player}_{color}"
        if file_key not in file_handles:
            file_path = os.path.join(splitted_dir, f"{file_key}.pgn")
            file_handles[file_key] = open(file_path, 'a')
        return file_handles[file_key]

    def close_all_files():
        for file in file_handles.values():
            file.close()
        file_handles.clear()

    try:
        with open(pgn_file, 'r') as pgn:
            while (game := chess.pgn.read_game(pgn)) is not None:
                game_count += 1

                white = clean_player_name(game.headers.get('White'))
                black = clean_player_name(game.headers.get('Black'))

                pgn_export = game.accept(chess.pgn.StringExporter(headers=True))

                if white not in ignored_players:
                    file = get_file_handle(white, 'white')
                    file.write(pgn_export + "\n\n")

                if black not in ignored_players:
                    file = get_file_handle(black, 'black')
                    file.write(pgn_export + "\n\n")

                if game_count % max_games_before_closing == 0:
                    close_all_files()

    finally:
        close_all_files()
