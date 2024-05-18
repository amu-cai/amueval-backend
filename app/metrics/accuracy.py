from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class Accuracy(MetricBase):
    """
    Accuracy metric class.

    Parameters
    ----------
    normalize : bool, default True
        Return the fraction of correctly classified samples, otherwise their
        number.
    sample_weight : list[Any] | None, default None
        Sample weights.
    """

    normalize: bool = True
    sample_weight: list[Any] | None = None

    def info(self) -> dict:
        return {
            "name": "accuracy",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score",
            "parameters": [
                {"name": "normalize", "data_type": "bool", "default_value": "True"},
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
            ],
        }

    def calculate(
        self,
        expected: list[Any],
        out: list[Any],
    ) -> float | int:
        """
        Metric calculation.

        Parameters
        ----------
        expected : list[Any]
            List with expected values.
        out : list[Any]
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
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
