from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class HingeLoss(MetricBase):
    """
    Hinge loss metric class.

    Parameters
    ----------
    labels : list[Any] | None, default None
        Contains all the labels for the problem. Used in multiclass hinge loss.
    sample_weight : list[Any] | None, default None
        Sample weights.
    """

    labels: list[Any] | None = None
    sample_weight: list[Any] | None = None

    def info(self) -> dict:
        return {
            "name": "Hinge loss",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.hinge_loss.html#sklearn.metrics.hinge_loss",
            "parameters": [
                {
                    "name": "labels",
                    "data_type": "list[Any] | None",
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
            return sk_metrics.hinge_loss(
                y_true=expected,
                pred_decision=out,
                labels=self.labels,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
