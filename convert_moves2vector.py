import os
import pickle
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed

from settings import SETTINGS

connection_string = f"mongodb://{SETTINGS['mongo']['host']}:{SETTINGS['mongo']['port']}"
client = MongoClient(connection_string)
db = client[SETTINGS['mongo']['database']]
collection = db[SETTINGS['mongo']['collection']]


def convert_dir(directory, batch_size=1000):
    collection.delete_many({})
    file_paths = [os.path.join(directory, file_name) for file_name in os.listdir(directory) if
                  os.path.isfile(os.path.join(directory, file_name))]
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(convert_file, fp): fp for fp in batch}
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
                first_year = int(min([int(x[0]) for x in move_data_list]))

                for i in range(len(move_data_list)):
                    prev_years = [
                        [int(x[0]), x[1], x[2]] for x in move_data_list
                        if int(x[0]) < int(move_data_list[i][0]) and move_data_list[i][2] > 0
                    ]  # Ensure conversion to int

                    if len(prev_years) > 0:
                        documents.append({
                            'input': prev_years,
                            'output': move_data_list[i][2],
                            'year': int(move_data_list[i][0]),
                            'first_year': first_year
                        })

        return documents


if __name__ == "__main__":
    convert_dir(SETTINGS['analyzed_games'])
