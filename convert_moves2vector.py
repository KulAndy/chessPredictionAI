import os
import pickle
from datetime import datetime

from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed

from settings import SETTINGS

connection_string = f"mongodb://{SETTINGS['mongo']['host']}:{SETTINGS['mongo']['port']}"
client = MongoClient(connection_string)
db = client[SETTINGS['mongo']['database']]
collection = db[SETTINGS['mongo']['collection']]


def convert_dir(directory, batch_size=1000):
    collection.drop()
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
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


def convert_file(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
        documents = []

        for fen, fen_data in data.items():
            last_year = 0
            for move, move_data_list in fen_data.items():
                included_years = [int(x[0]) for x in move_data_list]
                first_year = int(min(included_years))
                last_year_tmp = int(max(included_years))
                if last_year_tmp-first_year > 120:
                    continue
                last_year = max(last_year_tmp, last_year)

            for move, move_data_list in fen_data.items():
                included_years = [int(x[0]) for x in move_data_list]
                first_year = int(min(included_years))
                last_year_tmp = int(max(included_years))
                if last_year_tmp-first_year > 120:
                    continue
                filled_year = []
                for i in range(first_year, last_year):
                    if i not in included_years:
                        filled_year.append([i, 0, 0])
                data = sorted(move_data_list[:-120] + filled_year, key=lambda x: x[0])
                time_series = [rest for x, *rest in data]

                if len(time_series) > 1:
                    documents.append({
                        'series': time_series,
                        'first_year': first_year,
                        'last_year': last_year
                    })
        return documents


if __name__ == "__main__":
    convert_dir(SETTINGS['analyzed_games'])
