from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
import numpy as np
import xgboost as xgb
import os
from dotenv import load_dotenv
from google.cloud import storage
import tempfile

load_dotenv()  # Loads environment variables from .env file

app = FastAPI()

# Load model from Google Cloud Storage or local if env not set
def download_model_from_gcs():
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    blob_name = os.getenv("GCS_BLOB_NAME")
    if not bucket_name or not blob_name:
        raise ValueError("GCS_BUCKET_NAME and GCS_BLOB_NAME env vars must be set")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    blob.download_to_filename(temp_file.name)
    return temp_file.name

# Load model once at startup
MODEL_PATH = None
try:
    MODEL_PATH = download_model_from_gcs()
except Exception as e:
    print(f"Failed to load model from GCS: {e}")
    # Fallback to local file (for local dev)
    if os.path.exists("penguin_model.json"):
        MODEL_PATH = "penguin_model.json"
    else:
        raise RuntimeError("No model available")

model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)

class PenguinFeatures(BaseModel):
    bill_length_mm: float = Field(..., ge=0)
    bill_depth_mm: float = Field(..., ge=0)
    flipper_length_mm: float = Field(..., ge=0)
    body_mass_g: float = Field(..., ge=0)

    @validator('*')
    def check_not_negative(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v

@app.post("/predict")
def predict(features: PenguinFeatures):
    data = np.array([[features.bill_length_mm,
                      features.bill_depth_mm,
                      features.flipper_length_mm,
                      features.body_mass_g]])
    pred = model.predict(data)[0]
    return {"prediction": int(pred)}
