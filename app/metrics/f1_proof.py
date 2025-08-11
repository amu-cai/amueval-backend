import json
from fastapi import HTTPException
from collections import Counter
from typing import Callable

from metrics.metric_base import MetricBase


class F1Proof(MetricBase):
    """
    F1 Proofreading metric class.

    Parameters
    ----------
    weights : tuple[float] | list[tuple[float]], default (0.25, 0.25, 0.25, 0.25)
        Weights for unigrams, bigrams, trigrams and so on.
    smoothing_function : Callable | None, default None
    auto_reweigh : bool, default False
        Option to re-normalize the weights uniformly.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    weights: tuple[float] = (0.25, 0.25, 0.25, 0.25)
    smoothing_function: Callable | None = None
    auto_reweigh: bool = False
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "F1Proof",
            "link": "https://www.nltk.org/api/nltk.translate.bleu_score.html",
            "parameters": [
                {
                    "name": "weights",
                    "data_type": "tuple[float] | list[tuple[float]]",
                    "default_value": "(0.25, 0.25, 0.25, 0.25)",
                },
                {
                    "name": "smoothing_function",
                    "data_type": "Callable",
                    "default_value": "None",
                },
                {
                    "name": "auto_reweigh",
                    "data_type": "bool",
                    "default_value": "False",
                },
            ],
        }

    def calculate(
        self,
        references: list[list[str]],
        hypothesis: list[str],
    ) -> float | list[float]:
        """
        Metric calculation.

        Parameters
        ----------
        references : list[list[str]]
            List with reference sentences.
        hypothesis : list[str]
            List with hypothesis sentence.

        Returns
        -------
        Value of the metric.
        """
        try:
            refs = [json.loads(r.strip()) for r in references if r.strip()]
            hyps = [json.loads(h.strip()) for h in hypothesis if h.strip()]

            results = compare_with_gold(references, hypothesis)
            metric_results = printing_results(results)

            return metric_results["f1"]*100
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )



def printing_results(out_dc: dict):
    tp = out_dc['TP']
    fp = out_dc['FP']
    fn = out_dc['FN']

    if tp + fp == 0:
        precision = 0.0
    else:
        precision = tp / (tp + fp)

    if tp + fn == 0:
        recall = 0.0
    else:
        recall = tp / (tp + fn)
    fscore = (2 * precision * recall) / (precision + recall)

    return {'precision': precision, 'recall': recall, 'f1': fscore}


def filter_elements(lst1, lst2):
    count = Counter(lst2)
    result = []

    for item in lst1:
        if count[item] > 0:
            count[item] -= 1
        else:
            result.append(item)
    return result


def find_longest_list(list_of_lists):
    if not list_of_lists:
        return []

    return max(list_of_lists, key=len)



def compare_with_gold(json_gold_ls: list, json_llm_ls: list):
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    llm_by_id = {r["ipis_id"]: r for r in json_llm_ls}

    for gold_dc in json_gold_ls:
        normal_targets = gold_dc['normalised_target']
        normal_source = gold_dc['normalised_source']

        gid = gold_dc["ipis_id"]
        llm_dc = llm_by_id.get(gid)

        normal_answer = llm_dc['normalised_target']

        source = Counter(normal_source)

        # 1st step --
        if len(normal_targets) > 1:
            intersection = (Counter(normal_targets[0]) & Counter(normal_targets[1]) & Counter(
                normal_answer))
        else:
            intersection = (Counter(normal_targets[0]) & Counter(normal_answer))

        # poprawnie zmienione (tp)
        popr_zmien = intersection - source

        # poprawnie niezmienione + maskulatywy (tn)
        popr_niezmien = intersection - popr_zmien

        tp += len(list(popr_zmien.elements()))
        tn += len(list(popr_niezmien.elements()))

        # fp
        normal_answer = filter_elements(filter_elements(normal_answer, popr_zmien), popr_niezmien)
        fp += len(normal_answer)

        # fn
        normal_targets = [filter_elements(nntt, popr_niezmien) for nntt in
                          [filter_elements(nt, popr_zmien) for nt in normal_targets]]
        if [] in normal_targets:
            pass
        else:
            niepopr_niezmien = find_longest_list(normal_targets)
            fn += len(niepopr_niezmien)

    return {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn}