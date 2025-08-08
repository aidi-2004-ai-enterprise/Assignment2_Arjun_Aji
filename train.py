import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import seaborn as sns

def train_and_save_model():
    # Load dataset
    penguins = sns.load_dataset('penguins').dropna()

    # Features and target
    X = penguins[['bill_length_mm', 'bill_depth_mm', 'flipper_length_mm', 'body_mass_g']]
    y = penguins['species']

    # Encode target labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42)

    # Train model
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
    model.fit(X_train, y_train)

    # Save model to JSON
    model.save_model("penguin_model.json")
    print("Model saved as penguin_model.json")

if __name__ == "__main__":
    train_and_save_model()
