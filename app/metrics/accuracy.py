from sklearn import metrics as sk_metrics

from .metric_base import MetricBase


class Accuracy(MetricBase):
    """
    Accuracy metric class.

    Parameters
    ----------
    normalize : bool, default True
        Return the fraction of correctly classified samples, otherwise their
        number.
    sample_weight : list[float] | None, default None
        Sample weights.
    """

    normalize: bool = True
    sample_weight: list | None = None

    def info(self) -> dict:
        return {
            "name": "accuracy",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score",
            "parameters": [
                "normalize: bool (default True)",
                "sample_weight: list | None (default None)"
            ]
        }

    def calculate(
        self,
        expected: list[int],
        out: list[int],
    ) -> float | int:
        """
        Metric calculation.

        Parameters
        ----------
        expected : list[int]
            List with expected values.
        out : list[int]
            List with actual values.

        Returns
        -------
        Value of the metric.
        """
        try:
            return sk_metrics.accuracy_score(
                y_true=expected,
                y_pred=out,
                normalize=self.normalize,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            print(f"Could not calculate score because of error: {e}")
