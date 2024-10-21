import tensorflow as tf
# import tensorflowjs as tfjs
from settings import SETTINGS


def convert2complete_model():
    model = tf.keras.models.load_model(SETTINGS['model_dir'] + '/model.keras')

    model.save(SETTINGS['model_dir'] +'/complete_model.h5')

    # tfjs.converters.save_keras_model(model, 'model_js')


if __name__ == '__main__':
    convert2complete_model()
