from fastapi import HTTPException
from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class D2Tweedie(MetricBase):
    """
    D2 Tweedie score metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    power : float, default 0.0
        Tweedie power parameter. Either power <= 0 or power >= 1. The higher
        power the less weight is given to extreme deviations between true and
        predicted targets.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    sample_weight: list[Any] | None = None
    power: float = 0.0
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "d2 Tweedie score",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html#sklearn.metrics.d2_tweedie_score",
            "parameters": [
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {"name": "power", "data_type": "float", "default_value": "0.0"},
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
            return sk_metrics.d2_tweedie_score(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
                power=self.power,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
