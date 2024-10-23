from pymongo import MongoClient
from settings import SETTINGS
import os
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

connection_string = f"mongodb://{SETTINGS['mongo']['host']}:{SETTINGS['mongo']['port']}"
client = MongoClient(connection_string)
db = client[SETTINGS['mongo']['database']]
collection = db[SETTINGS['mongo']['collection']]

strategy = tf.distribute.MirroredStrategy()


def learn(batch_size=300_000):
    docs_count = collection.count_documents({})
    batch_start = 0

    with strategy.scope():
        model = None
        input_shape = (None, 3)

        while batch_start < docs_count:
            print(f"Processing batch {batch_start} to {batch_start + batch_size}")
            docs = collection.find({}).skip(batch_start).limit(batch_size)
            x_train = []
            y_train = []

            for doc in docs:
                input_data = np.array(doc['input'])  # array of 3D vectors, coords between 0 and 1
                output_data = np.array(doc['output'])  # float between 0 and 1

                output_data = np.log(output_data + 1e-8)

                x_train.append(input_data)
                y_train.append(output_data)

            x_train = tf.keras.preprocessing.sequence.pad_sequences(x_train, padding='post', dtype='float32', value=0.0)
            y_train = np.array(y_train)

            dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
            dataset = dataset.shuffle(buffer_size=len(x_train)).batch(256).prefetch(tf.data.AUTOTUNE)

            if model is None:
                model = models.Sequential()
                model.add(layers.Input(shape=input_shape))
                model.add(layers.TimeDistributed(layers.Dense(32, activation='relu')))
                model.add(layers.GlobalAveragePooling1D())

                model.add(layers.Dense(1, activation='sigmoid'))

                model.compile(optimizer='adam', loss='mse')
                model.summary()

            model.fit(dataset, epochs=10)

            if batch_start + batch_size < docs_count:
                print(f"Testing on next batch {batch_start + batch_size} to {batch_start + 2 * batch_size}")
                test_docs = collection.find({}).skip(batch_start + batch_size).limit(batch_size)
                x_test = []
                y_test = []

                for doc in test_docs:
                    input_data = np.array(doc['input'])
                    output_data = np.array(doc['output'])

                    output_data = np.log(output_data + 1e-8)

                    x_test.append(input_data)
                    y_test.append(output_data)

                x_test = tf.keras.preprocessing.sequence.pad_sequences(x_test, padding='post', dtype='float32',
                                                                       value=0.0)
                y_test = np.array(y_test)

                test_dataset = tf.data.Dataset.from_tensor_slices((x_test, y_test))
                test_dataset = test_dataset.batch(256).prefetch(tf.data.AUTOTUNE)

                loss = model.evaluate(test_dataset)
                print(f"Test loss: {loss}")

                model.fit(test_dataset, epochs=1)

            batch_start += batch_size

        if not os.path.exists(SETTINGS['model_dir']):
            os.mkdir(SETTINGS['model_dir'])

        model.save(SETTINGS['model_dir'] + '/model.keras')


def load_and_predict(new_data):
    model = tf.keras.models.load_model(SETTINGS['model_dir'] + '/model.keras')
    predictions = model.predict(new_data)
    return predictions


if __name__ == '__main__':
    new_data = np.random.rand(2, 5, 3)
    # print(new_data)
    # predictions = load_and_predict(new_data)
    # print(f"Predictions on new data: {predictions}")
    # for x in predictions:
    #     for value in x:
    #         print(f"{value:.10f}")
    test_set = np.array([
        [[0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0.1, 0.1, 0.1]],
        [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]],
        [[1, 1, 1], [0.9, 0.9, 0.9]],
        [[1, 1, 1], [1, 1, 1]]
    ])
    predictions = load_and_predict(test_set)
    print(f"Predictions on new data: {predictions}")
    for x in predictions:
        for value in x:
            print(f"{value:.10f}")
    test_set2 = np.array([
        [[0.49, 0.49, 0.49], [0.5, 0.5, 0.5], [0.51, 0.51, 0.51]]
    ])
    predictions = load_and_predict(test_set2)
    print(f"Predictions on new data: {predictions}")
    for x in predictions:
        for value in x:
            print(f"{value:.10f}")
