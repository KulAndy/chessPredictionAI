import os
import chess.pgn
import chess
from collections import defaultdict
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np


def analyze_dir(directory, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    file_paths = [
        os.path.join(directory, file_name)
        for file_name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file_name))
    ]

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(analyze_file, file_path, out_dir): file_path for file_path in file_paths}
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


def analyze_file(filename, out_dir):
    file_name_without_ext = os.path.splitext(os.path.basename(filename))[0]
    color = file_name_without_ext.split("_")[-1]

    if os.path.exists(f"{out_dir}/{file_name_without_ext}.pkl"):
        return True

    results = process_pgn(filename, None if color == "none" else color)

    # Convert the defaultdict to a regular dict before pickling
    results_dict = {fen: dict(year_data) for fen, year_data in results.items()}
    for fen in results_dict:
        results_dict[fen] = {move: list(data) for move, data in results_dict[fen].items()}

    with open(f"{out_dir}/{file_name_without_ext}.pkl", 'wb') as out:
        pickle.dump(results_dict, out)
    return True


def process_pgn(file_path, color=None):
    games_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"games": 0, "points": 0})))
    years = []

    with open(file_path, "r") as pgn_file:
        while (game := chess.pgn.read_game(pgn_file)) is not None:
            year = game.headers.get("Date", 'Unknown')[:4]
            if year.isdigit():
                int_year = int(year)
                years.append(int_year)
                board = game.board()
                result = game.headers.get("Result")

                try:
                    for move in game.mainline_moves():
                        fen = " ".join(board.fen().split(" ")[:-2])
                        if board.is_legal(move):
                            if (color == "white" and board.turn == chess.WHITE) or \
                                    (color == "black" and board.turn == chess.BLACK) or \
                                    color is None:
                                games_data[fen][int_year][move.uci()]["games"] += 1
                                games_data[fen][int_year][move.uci()]["points"] += get_points(result, board.turn)
                            board.push(move)
                        else:
                            break
                except Exception as e:
                    print(f"Error processing move: {e}")
                    continue

    return calculate_percentage_and_points(games_data, years)


def get_points(result, color):
    if result == "1-0":
        return 1 if color == chess.WHITE else 0
    elif result == "0-1":
        return 1 if color == chess.BLACK else 0
    elif result == "1/2-1/2":
        return 0.5
    return 0


def calculate_percentage_and_points(games_data, years):
    final_data = defaultdict(
        lambda:
        defaultdict(
            lambda:
            defaultdict(
                lambda: [0, 0]
            )
        )
    )

    for fen, years_data in games_data.items():
        for year, moves in years_data.items():
            year_int = int(year)
            for move, data in moves.items():
                games = data["games"]
                points = data["points"]

                total_games = sum(move_data["games"] for move_data in moves.values())
                percentage = games / total_games if total_games > 0 else 0
                avg_points = points / games if games > 0 else 0

                final_data[fen][move][year_int] = [avg_points, percentage]

    for fen, moves in final_data.items():
        for move, year_data in moves.items():
            years_arr = np.array(list(year_data.keys()), dtype=int)  # Ensure years are integers
            data_arr = np.array([data for data in year_data.values()])

            final_data[fen][move] = [
                [years_arr[i], *data_arr[i]] for i in range(len(years_arr))
            ]

    return final_data




