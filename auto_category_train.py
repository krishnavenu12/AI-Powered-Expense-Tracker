# auto_category_train.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# ✅ Load your CSV file
df = pd.read_csv("expense_samples.csv")  # Make sure this file is in the same folder

# ✅ Build the classification pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression())
])

# ✅ Train the model
model.fit(df["title"], df["category"])

# ✅ Save the trained model
joblib.dump(model, "category_classifier.pkl")
print("✅ Model trained and saved as category_classifier.pkl")
