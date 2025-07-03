from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import os
from train_sync import create_model, train_model, get_weights, set_weights, gossip_sync

app = FastAPI()
model = create_model()

class SyncRequest(BaseModel):
    peer: str

@app.post("/train")
def train():
    x = np.random.rand(50, 1)
    y = 2 * x + 1 + np.random.randn(50, 1) * 0.1
    train_model(x, y, model)
    return {"status": "trained"}

@app.get("/weights")
def weights():
    return get_weights(model)

@app.post("/sync")
def sync(req: SyncRequest):
    gossip_sync(req.peer, model)
    return {"status": f"synced with {req.peer}"}

@app.post("/sync-all")
def sync_all():
    peers = os.environ.get("PEERS", "").split(',')
    for peer in peers:
        if peer:
            gossip_sync(peer.strip(), model)
    return {"status": "gossip sync done"}