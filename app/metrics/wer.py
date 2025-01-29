from fastapi import HTTPException
from metrics.metric_base import MetricBase
from jiwer import wer


class WER(MetricBase):
    """
    Word error rate class.

    Parameters
    ----------
    sorting: str, default "descending"
        Information about the value of the metric.
    """

    sorting: str = "descending"

    def info(self) -> dict:
        return {
            "name": "word error rate",
            "link": "https://github.com/jitsi/jiwer/blob/master/docs/usage.md",
            "parameters": [
                {
                    "name": "dummy_param",
                    "data_type": "None",
                    "default_value": "None",
                },
            ],
        }

    def calculate(
        self,
        references: list[str],
        hypotheses: list[str],
    ) -> float:
        """
        Metric calculation.

        Parameters
        ----------
        references : list[str]
            List with reference sentences.
        hypotheses : list[str]
            List with hypothesis sentences.

        Returns
        -------
        Value of the metric.
        """
        try:
            return wer(references, hypotheses)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
