import os
import pickle
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed

from settings import SETTINGS

connection_string = f"mongodb://{SETTINGS['mongo']['host']}:{SETTINGS['mongo']['port']}"
client = MongoClient(connection_string)
db = client[SETTINGS['mongo']['database']]
collection = db[SETTINGS['mongo']['collection']]


def convert_dir(directory):
    collection.delete_many({})
    file_paths = [os.path.join(directory, file_name) for file_name in os.listdir(directory) if
                  os.path.isfile(os.path.join(directory, file_name))]

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(convert_file, file_path): file_path for file_path in file_paths}
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                documents = future.result()
                if documents:
                    collection.insert_many(documents)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")


def convert_file(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
        documents = []

        for fen, fen_data in data.items():
            for move, move_data_list in fen_data.items():
                for i in range(len(move_data_list)):
                    prev_years = [x for x in move_data_list if x[0] < move_data_list[i][0]]
                    if len(prev_years) > 0:
                        documents.append({
                            'input': prev_years,
                            'output': move_data_list[i][2]
                        })

        return documents


if __name__ == "__main__":
    convert_dir(SETTINGS['analyzed_games'])
