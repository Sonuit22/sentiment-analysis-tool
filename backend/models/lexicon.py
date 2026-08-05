import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

try:
    from backend.utils.preprocessing import normalize_text
except ImportError:
    from utils.preprocessing import normalize_text


class LexiconBaselineClassifier(BaseEstimator, ClassifierMixin):
    positive_words = {
        "good", "great", "excellent", "amazing", "awesome", "love", "happy", "best",
        "fantastic", "nice", "smooth", "fast", "helpful", "recommend", "satisfied",
        "premium", "bright", "reliable", "comfortable", "perfect", "value",
    }
    negative_words = {
        "bad", "worst", "awful", "hate", "angry", "delay", "poor", "terrible",
        "broken", "slow", "problem", "issue", "rude", "late", "cancelled",
        "damaged", "refund", "waste", "overpriced", "cheap", "buggy",
    }

    def fit(self, X, y):
        self.classes_ = np.array(sorted(pd.Series(y).dropna().astype(str).unique().tolist()))
        return self

    def predict(self, X):
        predictions = []
        classes = set(self.classes_)
        for text in X:
            tokens = normalize_text(text).split()
            pos = sum(token in self.positive_words for token in tokens)
            neg = sum(token in self.negative_words for token in tokens)
            if {"positive", "negative", "neutral"}.issubset(classes):
                if pos > neg:
                    predictions.append("positive")
                elif neg > pos:
                    predictions.append("negative")
                else:
                    predictions.append("neutral")
            else:
                predictions.append(self.classes_[0] if neg >= pos else self.classes_[-1])
        return np.array(predictions)


def train(texts, labels):
    model = LexiconBaselineClassifier()
    model.fit(texts, labels)
    return model


def predict(model, texts):
    return np.array(model.predict(texts))
