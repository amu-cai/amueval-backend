from fastapi import HTTPException
from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class Brier(MetricBase):
    """
    Brier metric class.

    Parameters
    ----------
    pos_label : int | float | bool | str | None, default None
        Label of the positive class.
    sample_weight : list[Any] | None, default None
        Sample weights.
    sorting: str, default "descending"
        Information about the value of the metric.
    """

    pos_label: int | float | bool | str | None = None
    sample_weight: list[Any] | None = None
    sorting: str = "descending"

    def info(self) -> dict:
        return {
            "name": "brier",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html#sklearn.metrics.brier_score_loss",
            "parameters": [
                {
                    "name": "pos_label",
                    "data_type": "int | float | bool | str | None",
                    "default_value": "None",
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
            return sk_metrics.brier_score_loss(
                y_true=expected,
                y_prob=out,
                pos_label=self.pos_label,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
