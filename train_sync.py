# train_and_sync.py
import requests
import numpy as np
import tensorflow as tf
from model import create_model

MODEL_PATH = "model.h5"

def train_model(x, y, model=None):
    if model is None:
        model = create_model()
    model.fit(x, y, epochs=1, verbose=0)
    return model

def get_weights(model):
    return model.get_weights()

def set_weights(model, weights):
    model.set_weights(weights)

def average_weights(w1, w2):
    return [(a + b) / 2.0 for a, b in zip(w1, w2)]

def gossip_sync(peer_url, model):
    try:
        local_weights = get_weights(model)
        peer_weights = requests.get(f"{peer_url}/weights").json()
        peer_weights = [np.array(w) for w in peer_weights]
        averaged = average_weights(local_weights, peer_weights)
        set_weights(model, averaged)
    except Exception as e:
        print("Gossip failed:", e)

