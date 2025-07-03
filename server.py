# server.py
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
from train_and_sync import create_model, get_weights, set_weights, train_model, gossip_sync

app = FastAPI()
model = create_model()

class WeightsIn(BaseModel):
    weights: list

@app.post("/train")
def train():
    x = np.random.rand(100, 1)
    y = 3 * x + np.random.randn(100, 1) * 0.1
    train_model(x, y, model)
    return {"message": "Model trained"}

@app.get("/weights")
def weights():
    return get_weights(model)

@app.post("/sync")
def sync(peer_url: str):
    gossip_sync(peer_url, model)
    return {"message": f"Synced with {peer_url}"}

