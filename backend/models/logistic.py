import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

try:
    from backend.utils.preprocessing import clean_text
except ImportError:
    from utils.preprocessing import clean_text


def train(texts, labels):
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                preprocessor=clean_text,
            )),
            ("model", LogisticRegression(max_iter=400, C=2.5)),
        ]
    )
    model.fit(texts, labels)
    return model


def predict(model, texts):
    return np.array(model.predict(texts))
