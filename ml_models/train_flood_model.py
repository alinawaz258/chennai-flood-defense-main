import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

# 1. Create dummy data for Chennai (Rainfall mm, Soil Moisture %, Drain Capacity %, Flooded)
data = {
    'rainfall_mm': [10, 50, 120, 5, 80, 150, 20, 100],
    'soil_moisture': [30, 60, 95, 20, 80, 99, 40, 85],
    'drain_capacity': [80, 50, 10, 90, 30, 5, 75, 20],
    'flooded': [0, 0, 1, 0, 1, 1, 0, 1] 
}
df = pd.DataFrame(data)

# 2. Separate features and target
X = df[['rainfall_mm', 'soil_moisture', 'drain_capacity']]
y = df['flooded']

# 3. Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)
print("Model trained successfully.")

# 4. Save the model for the backend to use
os.makedirs("ml_models/saved_models", exist_ok=True)
joblib.dump(model, "ml_models/saved_models/rf_flood_model.pkl")
print("Model saved to ml_models/saved_models/rf_flood_model.pkl")