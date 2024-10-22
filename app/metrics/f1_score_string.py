from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class F1String(MetricBase):
    """
    F1 score class for string predictions.

    Parameters
    ----------
    labels : list[Any] | None, default None
        The set of labels to include.
    pos_label : int | float | bool | str, default 1
        The class to report if average is binary and the data is binary.
    average : str | None, default 'binary'
        Possible values: ‘micro’, ‘macro’, ‘samples’, ‘weighted’, ‘binary’.
    sample_weight : list[Any] | None, default None
        Sample weights.
    zero_division : str | float | np.NaN, default 'warn'
        Sets the value to return when there is a zero division, i.e. when all
        predictions and labels are negative. Values: “warn”, 0.0, 1.0, np.nan.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    labels: list[Any] | None = None
    pos_label: int | float | bool | str = 1
    average: str | None = "binary"
    sample_weight: list[Any] | None = None
    zero_division: str | float = "warn"
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "f1 score",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html",
            "parameters": [
                {
                    "name": "labels",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {
                    "name": "pos_label",
                    "data_type": "int | float | bool | str",
                    "default_value": "1",
                },
                {
                    "name": "average",
                    "data_type": "str | None",
                    "default_value": "binary",
                    "possible_values": "micro, macro, samples, weighted, binary",
                },
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {
                    "name": "zero_division",
                    "data_type": "str | float | np.NaN",
                    "default_value": "warn",
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
            List with expected whitespace-separated string values.
        out : list[Any]
            List with actual whitespace-separated string values.

        Returns
        -------
        Value of the metric.
        """
        try:
            expected = [labels.split() for labels in expected]
            out = [labels.split() for labels in out]
            expected = [label for labels in expected for label in labels]
            out = [label for labels in out for label in labels]
            return sk_metrics.f1_score(
                y_true=expected,
                y_pred=out,
                labels=self.labels,
                pos_label=self.pos_label,
                average=self.average,
                sample_weight=self.sample_weight,
                zero_division=self.zero_division,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
