from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase
from metrics.gec_utils import score_gec


class PrecisionGEC(MetricBase):
    """
    Precision score class for Grammatical Error Correction (GEC).
    The scores are calculated using ERRANT from gec-metrics and support
    multiple references separated with X_CORRECTION_SPLIT_X.
    """

    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "Precision GEC score",
            "link": "https://github.com/gotutiyan/gec-metrics",
            "parameters": [
                {
                    "name": "dummy_param",
                    "data_type": "None",
                    "default_value": "None",
                }
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
            List with expected values in the format
            `source X_CORRECTION_SPLIT_X ref 1 X_CORRECTION_SPLIT_X ref 2 ...`.
        out : list[Any]
            List with actual values.

        Returns
        -------
        Value of the metric.
        """
        try:
            score = score_gec(expected, out, 1.0)
            return round(score.precision, 4)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
