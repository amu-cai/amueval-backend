from fastapi import HTTPException
from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class MeanAbsoluteError(MetricBase):
    """
    Mean absolute error metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    multioutput : str | list[Any], default 'uniform_average'
        Defines aggregating of multiple output scores. Values: 'raw_values',
        'uniform_average'.
    sorting: str, default "descending"
        Information about the value of the metric.
    """

    sample_weight: list[Any] | None = None
    multioutput: str | list[Any] = "uniform_average"
    sorting: str = "descending"

    def info(self) -> dict:
        return {
            "name": "mean absolute error",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html",
            "parameters": [
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {
                    "name": "multioutput",
                    "data_type": "str | list[Any]",
                    "default_value": "uniform_average",
                    "values": "raw_values, uniform_average",
                },
            ],
        }

    def calculate(
        self,
        expected: list[Any],
        out: list[Any],
    ) -> float | list[float]:
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
            return sk_metrics.mean_absolute_error(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
                multioutput=self.multioutput,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
