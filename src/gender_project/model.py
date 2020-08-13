from sklearn.base import TransformerMixin


class CategoryTransformer(TransformerMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fit(self, X):
        return self

    def transform(self, X):
        if (X is not None):
            return [str(x) for x in X]
        else:
            return None

    def fit_transform(self, X, y=None):
        return self.fit(X).transform(X)