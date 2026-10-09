from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase
from metrics.gec_utils import score_gec


class FBetaGEC(MetricBase):
    """
    F-beta score class for Grammatical Error Correction (GEC).
    The scores are calculated using ERRANT from gec-metrics and support
    multiple references separated with X_CORRECTION_SPLIT_X.

    Parameters
    ----------
    beta : float, default 1.0
        Ratio of recall importance to precision importance. beta > 1 gives more
        weight to recall, while beta < 1 favors precision.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    beta: float = 1.0
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "F1 GEC score",
            "link": "https://github.com/gotutiyan/gec-metrics",
            "parameters": [
                {
                    "name": "beta",
                    "data_type": "float",
                    "default_value": "1.0",
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
            score = score_gec(expected, out, self.beta)
            return round(score.f, 4)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
