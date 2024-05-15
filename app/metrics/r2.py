from sklearn import metrics as sk_metrics
from typing import Any

from metrics.metric_base import MetricBase


class R2(MetricBase):
    """
    R2 score metric class.

    Parameters
    ----------
    sample_weight : list[Any] | None, default None
        Sample weights.
    multioutput : str | list[Any], default 'uniform_average'
        Defines aggregating of multiple output scores. Values: 'raw_values',
        'uniform_average', 'variance_weighted'.
    force_finite : bool, default True
        Flag indicating if NaN and -Inf scores resulting from constant data
        should be replaced with real numbers (1.0 if prediction is perfect,
        0.0 otherwise).
    """

    sample_weight: list[Any] | None = None
    multioutput: str | list[Any] = "uniform_average"
    force_finite: bool = True

    def info(self) -> dict:
        return {
            "name": "r2 score",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html#sklearn.metrics.r2_score",
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
                    "values": "raw_values, uniform_average, variance_weighted",
                },
                {"name": "force_finite", "data_type": "bool", "default_value": "True"},
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
            return sk_metrics.r2_score(
                y_true=expected,
                y_pred=out,
                sample_weight=self.sample_weight,
                multioutput=self.multioutput,
                force_finite=self.force_finite,
            )
        except Exception as e:
            print(f"Could not calculate score because of error: {e}")
