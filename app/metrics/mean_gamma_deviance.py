from fastapi import HTTPException
from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class MeanGammaDeviance(MetricBase):
    """
    Mean gamma deviance metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    sorting: str, default "descending"
        Information about the value of the metric.
    """

    sample_weight: list[Any] | None = None
    sorting: str = "descending"

    def info(self) -> dict:
        return {
            "name": "mean gamma deviance",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_gamma_deviance.html#sklearn.metrics.mean_gamma_deviance",
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
            return sk_metrics.mean_gamma_deviance(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
