from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class MatthewsCorrelation(MetricBase):
    """
    Matthews correlation metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    sample_weight: list[Any] | None = None
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "Matthews correlation",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html#sklearn.metrics.matthews_corrcoef",
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
            return sk_metrics.matthews_corrcoef(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
