from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class HammingLoss(MetricBase):
    """
    Hamming loss metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    """

    sample_weight: list[Any] | None = None

    def info(self) -> dict:
        return {
            "name": "Hamming loss",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.hamming_loss.html#sklearn.metrics.hamming_loss",
            "parameters": [
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                }
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
            return sk_metrics.hamming_loss(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
