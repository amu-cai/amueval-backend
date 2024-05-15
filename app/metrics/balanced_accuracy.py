from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class BalancedAccuracy(MetricBase):
    """
    Balanced accuracy metric class.

    Parameters
    ----------
    adjusted : bool, default False
        When true, the result is adjusted for chance, so that random
        performance would score 0, while keeping perfect performance at a score
        of 1.
    sample_weight : list[Any] | None, default None
        Sample weights.
    """

    adjusted: bool = False
    sample_weight: list[Any] | None = None

    def info(self) -> dict:
        return {
            "name": "balanced accuracy",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html#sklearn.metrics.balanced_accuracy_score",
            "parameters": [
                {"name": "adjusted", "data_type": "bool", "default_value": "False"},
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
    ) -> float:
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
            return sk_metrics.balanced_accuracy_score(
                y_true=expected,
                y_pred=out,
                adjusted=self.adjusted,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
