import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

try:
    from backend.utils.preprocessing import clean_text
except ImportError:
    from utils.preprocessing import clean_text


def train(texts, labels):
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=2,
                preprocessor=clean_text,
            )),
            ("model", LinearSVC(C=0.8)),
        ]
    )
    model.fit(texts, labels)
    return model


def predict(model, texts):
    return np.array(model.predict(texts))
