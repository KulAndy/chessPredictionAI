import pickle
import tkinter as tk
from tkinter import ttk
import chess
import urllib.parse
import tempfile

import requests
import os
import numpy as np

from analyze import analyze_file
from learning import load_and_predict
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

        self.fen_obj={}

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Combobox(self.master, textvariable=self.input_var)
        self.input_entry['values'] = [
        ]
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

        self.draw_board()

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

        print(temp_file.name)

        with open(temp_file.name, 'w') as file:
            file.write(pgn)

        temp_file.close()
        temp_dir = tempfile.TemporaryDirectory()

        analyze_file(temp_file.name, temp_dir.name)
        file_name_without_ext = os.path.splitext(os.path.basename(temp_file.name))[0]
        print(f"{temp_dir.name}/{file_name_without_ext}.pkl")

        with open(f"{temp_dir.name}/{file_name_without_ext}.pkl", 'rb') as file:
            self.fen_obj = pickle.load(file)

        self.predicate()

        os.remove(temp_file.name)
        temp_dir.cleanup()

    def predicate(self):

        try:
            fen = " ".join(self.board.fen().split(" ")[:-2])
            for key in self.fen_obj[fen]:
                value = self.fen_obj[fen][key]
                predictions = load_and_predict(np.array([value]))
                print(f"{key}: {predictions[0][0]}")

        except KeyError:
            pass


def row2pgn(row):
    return f"""[Event "{row["Event"]}"]
[Site "{row["Site"]}"]
[Date "{row["Year"]}.{row["Month"]or"??"}.{row["Day"] or "??"}"]
[Round "{row["Round"]}"]
[White "{row["White"]}"]
[Black "{row["Black"]}"]
[Result "{row["Result"]}"]

{row["moves"]}
"""


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
