from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
import xgboost as xgb
import numpy as np
from fastapi.testclient import TestClient

# Define the FastAPI app within the test file for testing purposes
app = FastAPI()

# Load model locally (simplified for Colab testing)
# Make sure the model file 'penguin_model.json' exists in the same directory
model = xgb.XGBClassifier()
try:
    model.load_model("penguin_model.json")
except xgb.core.XGBoostError:
    # Handle case where model file might not be found during testing
    print("Warning: penguin_model.json not found. Model loading skipped for tests.")
    model = None # Or a mock model if needed for tests that don't require loading

class PenguinFeatures(BaseModel):
    bill_length_mm: float = Field(..., ge=0)
    bill_depth_mm: float = Field(..., ge=0)
    flipper_length_mm: float = Field(..., ge=0)
    body_mass_g: float = Field(..., ge=0)

    @validator('*', pre=True) # Removed each_item=True
    def check_not_negative(cls, v):
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError('Value must be non-negative')
        return v

@app.post("/predict")
def predict(features: PenguinFeatures):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    data = np.array([[features.bill_length_mm,
                      features.bill_depth_mm,
                      features.flipper_length_mm,
                      features.body_mass_g]])
    pred = model.predict(data)[0]
    # Note: The original model output is a class index (0, 1, or 2).
    # If you want to return the actual species name, you'll need the LabelEncoder
    # or a mapping from index to species name available here as well.
    # For simplicity, returning the index as an integer.
    return {"prediction": int(pred)}


client = TestClient(app)

def test_predict_endpoint_valid_input():
    sample_data = {
        "bill_length_mm": 39.1,
        "bill_depth_mm": 18.7,
        "flipper_length_mm": 181,
        "body_mass_g": 3750
    }
    response = client.post("/predict", json=sample_data)
    assert response.status_code == 200
    assert "prediction" in response.json()
    # You might want to add checks on the predicted value range (0, 1, or 2)

def test_predict_endpoint_missing_field():
    sample_data = {
        "bill_length_mm": 39.1,
        "bill_depth_mm": 18.7,
        "flipper_length_mm": 181
        # Missing body_mass_g
    }
    response = client.post("/predict", json=sample_data)
    assert response.status_code == 422

def test_predict_endpoint_invalid_type():
    sample_data = {
        "bill_length_mm": "invalid",  # should be float
        "bill_depth_mm": 18.7,
        "flipper_length_mm": 181,
        "body_mass_g": 3750
    }
    response = client.post("/predict", json=sample_data)
    assert response.status_code == 422

def test_predict_endpoint_out_of_range():
    sample_data = {
        "bill_length_mm": 500,  # unrealistic but accepted if >=0
        "bill_depth_mm": 18.7,
        "flipper_length_mm": 181,
        "body_mass_g": -50  # negative not allowed
    }
    response = client.post("/predict", json=sample_data)
    assert response.status_code == 422  # Validator catches negative value
