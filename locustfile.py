from locust import HttpUser, task, between
import random

class PredictUser(HttpUser):
    wait_time = between(1, 3)  # wait between requests

    @task
    def predict(self):
        payload = {
            "bill_length_mm": round(random.uniform(35, 55), 1),
            "bill_depth_mm": round(random.uniform(13, 20), 1),
            "flipper_length_mm": round(random.uniform(170, 230), 1),
            "body_mass_g": round(random.uniform(3000, 6000), 1),
            "sex": random.choice(["Male", "Female"])
        }
        self.client.post("/predict", json=payload)
