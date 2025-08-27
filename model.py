import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf

# # === Model ===
def create_model(input_shape=561, num_classes=6):
    with tf.device('/CPU:0'):
        model = tf.keras.Sequential([
            tf.keras.Input(shape=(input_shape,)),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model