import tkinter as tk
from tkinter import ttk
import chess
import urllib.parse

import requests

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
                print("FEN:", self.board.fen())
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
        url = SETTINGS["API"]["search_games"] + urllib.parse.quote(input_value) + "/" + urllib.parse.quote(selected_color)
        print(url)
        res = requests.get(url)
        print(res.json())


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
