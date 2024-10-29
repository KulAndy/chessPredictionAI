import math
import pickle
import tkinter as tk
from tkinter import ttk
import chess
import urllib.parse
import tempfile

import requests
import os
import numpy as np
from datetime import datetime

from analyze import analyze_file
from learning import load_and_predict, normalize_year
from settings import SETTINGS

CHESS_PIECES = {
    "p": "♟",
    "r": "♜",
    "n": "♞",
    "b": "♝",
    "q": "♛",
    "k": "♚",
    "P": "♙",
    "R": "♖",
    "N": "♘",
    "B": "♗",
    "Q": "♕",
    "K": "♔",
}


class ChessApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Chess Board")
        self.board = chess.Board()
        self.selected_square = None

        self.fen_obj = {}
        self.predictions = []

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Combobox(self.master, textvariable=self.input_var)
        self.input_entry['values'] = []
        self.input_entry.set("")
        self.input_entry.pack(pady=10)

        self.input_entry.bind('<KeyRelease>', self.on_keyrelease)

        self.color_var = tk.StringVar(value="white")  # Default to white
        tk.Radiobutton(self.master, text="White", variable=self.color_var, value="white").pack(side=tk.TOP)
        tk.Radiobutton(self.master, text="Black", variable=self.color_var, value="black").pack(side=tk.TOP)

        self.submit_button = tk.Button(self.master, text="Submit", command=self.submit_input)
        self.submit_button.pack(pady=10)

        self.canvas = tk.Canvas(self.master, width=400, height=400)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        self.undo_button = tk.Button(self.master, text="Undo", command=self.undo_move)
        self.undo_button.pack(pady=10)

        self.prediction_frame = ttk.Frame(self.master)
        self.prediction_frame.pack(pady=10)

        self.scrollbar = ttk.Scrollbar(self.prediction_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.prediction_canvas = tk.Canvas(self.prediction_frame, yscrollcommand=self.scrollbar.set)
        self.prediction_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.prediction_canvas.yview)

        self.prediction_container = ttk.Frame(self.prediction_canvas)
        self.prediction_canvas.create_window((0, 0), window=self.prediction_container, anchor="nw")

        self.prediction_container.bind("<Configure>", self.on_frame_configure)

        self.draw_board()

    def undo_move(self):
        if self.board.move_stack:
            self.board.pop()
            self.draw_board()
            self.predicate()


    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#eee", "#ddd"]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                self.canvas.create_rectangle(col * 50, row * 50, (col + 1) * 50, (row + 1) * 50, fill=color)

                if self.selected_square is not None and self.selected_square == chess.square(col, 7 - row):
                    self.canvas.create_rectangle(col * 50, row * 50, (col + 1) * 50, (row + 1) * 50, outline="red",
                                                 width=3)

        self.draw_pieces()

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row, col = divmod(square, 8)
                self.canvas.create_text(col * 50 + 25, (7 - row) * 50 + 25, text=CHESS_PIECES[piece.symbol()],
                                        font=("Arial", 32))

    def on_click(self, event):
        col = event.x // 50
        row = event.y // 50
        clicked_square = chess.square(col, 7 - row)

        if self.selected_square is None:
            if self.board.piece_at(clicked_square) and self.board.piece_at(clicked_square).color == self.board.turn:
                self.selected_square = clicked_square
        else:
            move = chess.Move(self.selected_square, clicked_square)
            if move in self.board.legal_moves:
                self.board.push(move)
                print("FEN:", " ".join(self.board.fen().split(" ")[:-2]))
                self.predicate()
            self.selected_square = None

        self.draw_board()

    def on_keyrelease(self, event):
        text = self.input_var.get()
        if len(text) >= 4:
            url = SETTINGS["API"]["search_player"] + urllib.parse.quote(text)
            res = requests.get(url)
            try:
                self.input_entry['values'] = res.json()
            except:
                self.input_entry['values'] = []
        else:
            self.input_entry['values'] = []

    def submit_input(self):
        input_value = self.input_var.get()
        selected_color = self.color_var.get()
        url = SETTINGS["API"]["search_games"] + urllib.parse.quote(input_value) + "/" + urllib.parse.quote(
            selected_color)

        try:
            res = requests.get(url)
            res.raise_for_status()  # Raises HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return

        data = res.json()
        pgn = "\n".join((row2pgn(x) for x in data))
        temp_file = tempfile.NamedTemporaryFile(suffix=f"{input_value}_none.pgn", delete=False)

        with open(temp_file.name, 'w') as file:
            file.write(pgn)

        temp_file.close()
        temp_dir = tempfile.TemporaryDirectory()

        analyze_file(temp_file.name, temp_dir.name)
        file_name_without_ext = os.path.splitext(os.path.basename(temp_file.name))[0]

        with open(f"{temp_dir.name}/{file_name_without_ext}.pkl", 'rb') as file:
            self.fen_obj = pickle.load(file)

        self.board = chess.Board()
        self.draw_board()

        self.predicate()

        os.remove(temp_file.name)
        temp_dir.cleanup()

    def predicate(self):
        self.predictions.clear()
        for widget in self.prediction_container.winfo_children():
            widget.destroy()

        try:
            fen = " ".join(self.board.fen().split(" ")[:-2])
            for key in self.fen_obj[fen]:
                value = self.fen_obj[fen][key]
                first_items = [x[0] for x in value]
                for i in range(min(first_items), datetime.now().year + 1):
                    if i not in first_items:
                        value.append([i, 0, 0])

                predictions = load_and_predict(
                    np.array(
                        [
                            normalize_year(value)
                        ]
                    )
                )
                prediction_value = predictions[0][0]
                print(f"{key} {prediction_value}")

                try:
                    log_value = 1 / (math.log(prediction_value, 1 / 1024) + 1)
                except:
                    log_value = 0
                print(f"{key} {log_value * 100}")
                self.predictions.append((key, prediction_value, log_value * 100))

            # Sort predictions in descending order by prediction_value
            self.predictions.sort(key=lambda x: x[1], reverse=True)

            for move, prediction_value, percent_value in self.predictions:
                row_frame = tk.Frame(self.prediction_container)
                row_frame.pack(fill=tk.X, pady=2)

                move_label = tk.Label(row_frame, text=move)
                move_label.pack(side=tk.LEFT, padx=5)

                progress = ttk.Progressbar(row_frame, orient="horizontal", length=300, mode="determinate")
                progress['value'] = percent_value
                progress.pack(side=tk.LEFT, padx=5)

            print("=" * 50)

        except KeyError:
            pass

    def on_frame_configure(self, event):
        self.prediction_canvas.configure(scrollregion=self.prediction_canvas.bbox("all"))

    def on_frame_configure(self, event):
        self.prediction_canvas.configure(scrollregion=self.prediction_canvas.bbox("all"))


def row2pgn(row):
    return f"""[Event "{row["Event"]}"]
[Site "{row["Site"]}"]
[Date "{row["Year"]}.{row["Month"] or "??"}.{row["Day"] or "??"}"]
[Round "{row["Round"]}"]
[White "{row["White"]}"]
[Black "{row["Black"]}"]
[Result "{row["Result"]}"]

{row["moves"]}\n"""


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
