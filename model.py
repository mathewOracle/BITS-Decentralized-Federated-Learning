import tensorflow as tf

def create_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(1, input_shape=(1,))
    ])
    model.compile(optimizer='sgd', loss='mean_squared_error')
    return model