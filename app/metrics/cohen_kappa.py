from fastapi import HTTPException
from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class CohenKappa(MetricBase):
    """
    Kohen cappa metric class.

    Parameters
    ----------
    labels : list[Any] | None, default None
        List of labels to index the matrix.
    weights : str | None, default None
        Weighting type to calculate the score. Values: 'linear', 'quadratic'.
    sample_weight : list[Any] | None, default None
        Sample weights.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    labels: list[Any] | None = None
    weights: str | None = None
    sample_weight: list[Any] | None = None
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "Cohen kappa",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html#sklearn.metrics.cohen_kappa_score",
            "parameters": [
                {
                    "name": "labels",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {
                    "name": "weights",
                    "data_type": "str | None",
                    "default_value": "None",
                    "values": "linear, quadratic",
                },
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
            return sk_metrics.cohen_kappa_score(
                y_true=expected,
                y_pred=out,
                labels=self.labels,
                weights=self.weights,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
