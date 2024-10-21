import asyncio
import sys
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox


class AIClient:
    def __init__(self, root):
        self.root = root
        self.root.title("AI client")

        self.input_trf_path = None
        self.cr_compare_value = tk.IntVar()

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.message_text = tk.Text(container, wrap="word", state="disabled")
        self.message_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(container, command=self.message_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.message_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.message_text.yview)

        self.cr_compare_label = tk.Label(root, text="Color")
        self.cr_compare_label.pack(anchor="w")

        self.cr_compare_option1 = tk.Radiobutton(root, text="White", variable=self.cr_compare_value, value=0)
        self.cr_compare_option2 = tk.Radiobutton(root, text="Black", variable=self.cr_compare_value, value=1)
        self.cr_compare_option1.pack(anchor="w")
        self.cr_compare_option2.pack(anchor="w")

        self.trf_label = tk.Label(root, text="PGN file")
        self.trf_label.pack(anchor="w")
        self.trf_button = tk.Button(root, text="Choose", command=self.browse_trf)
        self.trf_button.pack(anchor="w")

        self.url_label = tk.Label(root, text="Player")
        self.url_label.pack(anchor="w")
        self.url = tk.StringVar()
        self.url_input = tk.Entry(root, textvariable=self.url, width=50)
        self.url_input.pack(anchor="w")

        self.selected_trf_label = tk.Label(root, text="")
        self.selected_trf_label.pack(anchor="w")

        self.start_button = tk.Button(root, text="Predict", command=self.start_correction)
        self.start_button.pack()

        sys.stderr = LogStream(self.log_message, "red")
        sys.stdout = LogStream(self.log_message)

        self.clear_messages()
        self.loading = True
        threading.Thread(target=self.initialize_data).start()

    def browse_trf(self):
        self.input_trf_path = filedialog.askopenfilename(filetypes=[("raporty TRF", "*.txt")])
        self.selected_trf_label.config(text=self.input_trf_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = AIClient(root)
    root.mainloop()
