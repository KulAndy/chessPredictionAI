import tensorflow as tf
from tensorflow.keras import layers, models, mixed_precision
import numpy as np
import datetime
import os
from pymongo import MongoClient
from settings import SETTINGS
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

mixed_precision.set_global_policy('mixed_float16')

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.set_visible_devices(gpus[0], 'GPU')
        tf.config.experimental.set_memory_growth(gpus[0], True)
    except RuntimeError as e:
        print(f"Error setting up GPU memory growth: {e}")

connection_string = f"mongodb://{SETTINGS['mongo']['host']}:{SETTINGS['mongo']['port']}"
client = MongoClient(connection_string)
db = client[SETTINGS['mongo']['database']]
collection = db[SETTINGS['mongo']['collection']]

early_stopping = EarlyStopping(
    monitor='loss',
    patience=30,
    restore_best_weights=True,
)

reduce_lr = ReduceLROnPlateau(
    monitor='loss',
    factor=0.1,
    patience=10,
    min_lr=1e-7
)


def learn(batch_size=32768*8, epochs=1000, train_batch_size=128):
    log_dir = (SETTINGS.get('tensorboard_log_dir', 'logs/')
               + f"R2_M3_B1_{epochs}_{train_batch_size}_"
               + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
               )
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

    docs_count = collection.count_documents({})
    batch_start = 0

    model = None
    while batch_start < docs_count:
        print(f"Processing batch {batch_start} to {batch_start + batch_size}")
        docs = collection.find({}).skip(batch_start).limit(batch_size)
        x_train = []
        y_train = []

        for doc in docs:
            x_train.append(doc['series'][::-1])
            y_train.append(doc['series'][-1][0])

        x_train = tf.keras.preprocessing.sequence.pad_sequences(x_train, padding='post', dtype='float32', value=0)
        y_train = np.clip(np.array(y_train), 0, 1)

        dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
        dataset = dataset.shuffle(buffer_size=len(x_train)).batch(train_batch_size).prefetch(tf.data.AUTOTUNE)
        if model is None:
            input_shape = (None, 2)
            model = models.Sequential([
                layers.Input(shape=input_shape),

                layers.GRU(128, return_sequences=True),
                layers.Dropout(0.3),

                layers.GRU(64, return_sequences=True),
                layers.Dropout(0.3),

                layers.GRU(32, return_sequences=True),
                layers.TimeDistributed(layers.Dense(64, activation='relu')),
                layers.Dropout(0.3),

                layers.GlobalAveragePooling1D(),

                layers.Dense(32, activation='relu'),
                layers.Dropout(0.3),
                layers.Dense(16, activation='relu'),
                layers.Dense(8, activation='relu'),
                layers.Dense(4, activation='relu'),

                layers.Dense(1, activation='sigmoid')
            ])
            model.compile(optimizer='adam', loss='mse')

            model.summary()

        model.fit(dataset, epochs=epochs, callbacks=[tensorboard_callback, early_stopping, reduce_lr])
        batch_start += batch_size

    # Save the model after training
    if not os.path.exists(SETTINGS['model_dir']):
        os.mkdir(SETTINGS['model_dir'])

    model.save(SETTINGS['model_dir'] + '/model.keras')


# Load and predict
def load_and_predict(new_data):
    model = tf.keras.models.load_model(SETTINGS['model_dir'] + '/model.keras')
    predictions = model.predict(new_data)
    return predictions


# Main script
if __name__ == '__main__':
    new_data = np.random.rand(2, 5, 2)
    predictions = load_and_predict(new_data)
    print(f"Predictions on new data: {predictions}")
    for x in predictions:
        for value in x:
            print(f"{value:.10f}")

    test_set = np.array([
        [[0, 0], [0, 0]],
        [[0, 0], [0.1, 0.1]],
        [[0.1, 0.1], [0.2, 0.2]],
        [[0.5, 0.5], [0.5, 0.5]],
        [[1, 1], [0.9, 0.9]],
        [[1, 1], [1, 1]]
    ])
    predictions = load_and_predict(test_set)
    print(f"Predictions on test1 data: {predictions}")
    for x in predictions:
        for value in x:
            print(f"{value:.10f}")
    test_set2 = np.array([
        [[0.49, 0.49], [0.5, 0.5], [0.51, 0.51]]
    ])
    predictions = load_and_predict(test_set2)
    print(f"Predictions on test2 data: {predictions}")
    for x in predictions:
        for value in x:
            print(f"{value:.10f}")
