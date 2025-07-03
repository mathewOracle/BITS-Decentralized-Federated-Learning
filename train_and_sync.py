import numpy as np
import requests
from model import create_model

def train_model(x, y, model):
    history=model.fit(x, y, epochs=1, verbose=0)
    print("Loss:", history.history['loss'][0])
    return model, history.history['loss'][0]

def get_weights(model):
    return [w.tolist() for w in model.get_weights()]

def set_weights(model, weights):
    model.set_weights([np.array(w) for w in weights])

def average_weights(w1, w2):
    return [(np.array(a) + np.array(b)) / 2.0 for a, b in zip(w1, w2)]

def gossip_sync(peer_url, model):
    try:
        r = requests.get(f"http://{peer_url}/weights", timeout=3)
        peer_weights = r.json()
        peer_weights = [np.array(w) for w in peer_weights]
        averaged = average_weights(model.get_weights(), peer_weights)
        model.set_weights(averaged)
    except Exception as e:
        print(f"Failed to sync with {peer_url}: {e}")