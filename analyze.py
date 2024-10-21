import math
import os
import chess.pgn
import chess
from collections import defaultdict
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed


def analyze_dir(directory, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    file_paths = [os.path.join(directory, file_name) for file_name in os.listdir(directory) if
                  os.path.isfile(os.path.join(directory, file_name))]

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(analyze_file, file_path, out_dir): file_path for file_path in file_paths}
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                if future.result():
                    os.remove(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


def analyze_file(filename, out_dir):
    file_name_without_ext = os.path.splitext(os.path.basename(filename))[0]
    color = file_name_without_ext.split("_")[-1]
    if os.path.exists(f"{out_dir}/{file_name_without_ext}.pkl"):
        return True
    results = process_pgn(filename, color)
    # Convert the defaultdict to a regular dict before pickling
    results_dict = {fen: dict(year_data) for fen, year_data in results.items()}
    for fen in results_dict:
        results_dict[fen] = {move: list(data) for move, data in results_dict[fen].items()}
    with open(f"{out_dir}/{file_name_without_ext}.pkl", 'wb') as out:
        pickle.dump(results_dict, out)
    return True


def process_pgn(file_path, color):
    games_data = defaultdict(
        lambda:
        defaultdict(
            lambda:
            defaultdict(
                lambda: {"games": 0, "points": 0}
            )
        )
    )

    max_year = -math.inf
    min_year = math.inf
    with open(file_path, "r") as pgn_file:
        while (game := chess.pgn.read_game(pgn_file)) is not None:
            year = (game.headers.get("Date")[:4] if game.headers.get("Date") else 'Unknown')
            try:
                int_year = int(year)
            except ValueError:
                continue

            max_year = max(max_year, int_year)
            min_year = min(min_year, int_year)

            board = game.board()
            result = game.headers.get("Result")
            points = get_points(result, color)

            try:
                for move in game.mainline_moves():
                    fen = board.fen()

                    if board.is_legal(move):
                        if (color == "white" and board.turn == chess.WHITE) or (
                                color == "black" and board.turn == chess.BLACK):
                            games_data[fen][year][move.uci()]["games"] += 1
                            games_data[fen][year][move.uci()]["points"] += points
                        board.push(move)
                    else:
                        break
            except:
                pass

    return calculate_percentage_and_points(games_data, min_year, max_year)


def get_points(result, color):
    if result == "1-0":
        return 1 if color == "white" else 0
    elif result == "0-1":
        return 1 if color == "black" else 0
    elif result == "1/2-1/2":
        return 0.5
    return 0


def calculate_percentage_and_points(games_data, min_year, max_year):
    final_data = defaultdict(lambda: defaultdict(list))

    year_range = max_year - min_year + 1

    for fen, years_data in games_data.items():
        if not isinstance(years_data, dict):
            continue

        for year, moves in years_data.items():
            if not isinstance(moves, dict):
                continue

            for move, data in moves.items():
                if not isinstance(data, dict):
                    continue

                try:
                    year_int = int(year)
                except ValueError:
                    continue

                games = data["games"]
                points = data["points"]

                total_games = sum(move_data["games"] for move_data in moves.values())
                if total_games > 0:
                    percentage = games / total_games
                else:
                    percentage = 0
                avg_points = points / games if games > 0 else 0

                final_data[fen][move].append([(year_int - min_year + 1) / year_range, avg_points, percentage])

    return final_data
