import shutil
import os
import time

from convert_moves2vector import convert_dir
from learning import learn
from settings import SETTINGS
from split_pgn import split_pgn
from analyze import analyze_dir


def prepare_files():
    # pgn_file = "Giga.pgn"
    pgn_file = "tb_all.pgn"

    if os.path.exists(SETTINGS['splitted_pgns_dir']):
        shutil.rmtree(SETTINGS['splitted_pgns_dir'])
    os.mkdir(SETTINGS['splitted_pgns_dir'])
    split_pgn(pgn_file)


def main():
    print("Dzielenie pliku pgn")
    # prepare_files()
    print("podzielono")
    print("analiza plików")
    # analyze_dir(SETTINGS['splitted_pgns_dir'], SETTINGS['analyzed_games'])
    print("przeanalizowano")
    print("konwersja na wektory")
    # convert_dir(SETTINGS['analyzed_games'])
    print("skonwertowano")
    print("uczenie")
    learn()
    print("nauczono")


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Czas: {elapsed_time}s")
