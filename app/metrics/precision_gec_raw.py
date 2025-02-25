from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase
import errant
from collections import Counter
import re


class PrecisionGECRaw(MetricBase):
    """
    Precision score class for Grammatical Error Correction (GEC).
    The raw means that the strings are without punctuation and are lowercased.
    The scores are calculated using ERRANT.
    """

    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "Precision GEC score raw",
            "link": "https://github.com/chrisjbryant/errant",
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
            List with expected values.
        out : list[Any]
            List with actual values.

        Returns
        -------
        Value of the metric.
        """
        try:
            expected = [x.split("X_CORRECTION_SPLIT_X") for x in expected]
            sources = [x[0] for x in expected]
            targets = [x[1] for x in targets]

            out = [re.sub(r'[^a-zA-Z0-9 ]','', v.lower()) for v in out]
            sources = [re.sub(r'[^a-zA-Z0-9 ]','', v.lower()) for v in sources]
            targets = [re.sub(r'[^a-zA-Z0-9 ]','', v.lower()) for v in targets]

            best_dict, precision, recall, f_score = get_fbeta_score(out, targets, sources, 1)
            return precision
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )


def get_fbeta_score(preds, targets, sources, beta=1):
    annotator = errant.load('en')
    best_dict = Counter({"tp":0, "fp":0, "fn":0})

    for pred, target, source in zip(preds, targets, sources):
        parsed_pred = annotator.parse(pred, tokenise=True)
        parsed_target = annotator.parse(target, tokenise=True)
        parsed_source = annotator.parse(source, tokenise=True)

        edits_pred = annotator.annotate(parsed_source, parsed_pred)
        edits_target = annotator.annotate(parsed_source, parsed_target)

        simplified_pred_edits = []
        simplified_target_edits = []
        for e in edits_pred:
            simplified_pred_edits.append([e.o_start, e.o_end, e.type, e.c_str, 0])

        for e in edits_target:
            simplified_target_edits.append([e.o_start, e.o_end, e.type, e.c_str, 0])

        hyp_dict = process_edits(simplified_pred_edits)
        ref_dict = process_edits(simplified_target_edits)

        count_dict = evaluate_edits(hyp_dict, ref_dict, best_dict, beta)
        
        best_dict += Counter(count_dict)

    precision, recall, f_score = computeFScore(best_dict["tp"], best_dict["fp"], best_dict["fn"], beta)
    return best_dict, precision, recall, f_score


def simplify_edits(edits_m2):
    out_edits = []
    edits = edits_m2.split("\n")

    for edit in edits:
        edit = edit[2:].split("|||") # Ignore "A " then split.
        span = edit[0].split()
        start = int(span[0])
        end = int(span[1])
        cat = edit[1]
        cor = edit[2]
        coder = int(edit[-1])
        out_edit = [start, end, cat, cor, coder]
        out_edits.append(out_edit)

    return out_edits


def process_edits(edits):
    coder_dict = {}
    if not edits: 
        edits = [[-1, -1, "noop", "-NONE-", 0]]

    for edit in edits:
        start = edit[0]
        end = edit[1]
        cat = edit[2]
        cor = edit[3]
        coder = edit[4]

        if coder not in coder_dict: 
            coder_dict[coder] = {}

        if (start, end, cor) in coder_dict[coder].keys():
            coder_dict[coder][(start, end, cor)].append(cat)
        else:
            coder_dict[coder][(start, end, cor)] = [cat]

    return coder_dict


def evaluate_edits(hyp_dict, ref_dict, best, beta):
    # Store the best sentence level scores and hyp+ref combination IDs
    # best_f is initialised as -1 cause 0 is a valid result.
    best_tp, best_fp, best_fn, best_f, best_hyp, best_ref = 0, 0, 0, -1, 0, 0
    best_cat = {}

    for hyp_id in hyp_dict.keys():
        for ref_id in ref_dict.keys():
            tp, fp, fn = compareEdits(hyp_dict[hyp_id], ref_dict[ref_id])
            p, r, f = computeFScore(
                tp+best["tp"], fp+best["fp"], fn+best["fn"], beta)
            if     (f > best_f) or \
                (f == best_f and tp > best_tp) or \
                (f == best_f and tp == best_tp and fp < best_fp) or \
                (f == best_f and tp == best_tp and fp == best_fp and fn < best_fn):
                best_tp, best_fp, best_fn = tp, fp, fn
                best_f, best_hyp, best_ref = f, hyp_id, ref_id

    best_dict = {"tp":best_tp, "fp":best_fp, "fn":best_fn}

    return best_dict


def compareEdits(hyp_edits, ref_edits):
    tp = 0
    fp = 0
    fn = 0

    for h_edit, h_cats in hyp_edits.items():
        if h_cats[0] == "noop": 
            continue
        # TRUE POSITIVES
        if h_edit in ref_edits.keys():
            for h_cat in ref_edits[h_edit]:
                tp += 1
        # FALSE POSITIVES
        else:
            for h_cat in h_cats:
                fp += 1

    for r_edit, r_cats in ref_edits.items():
        if r_cats[0] == "noop": 
            continue
        # FALSE NEGATIVES
        if r_edit not in hyp_edits.keys():
            for r_cat in r_cats:
                fn += 1

    return tp, fp, fn


def computeFScore(tp, fp, fn, beta):
    p = float(tp)/(tp+fp) if fp else 1.0
    r = float(tp)/(tp+fn) if fn else 1.0
    f = float((1+(beta**2))*p*r)/(((beta**2)*p)+r) if p+r else 0.0

    return round(p, 4), round(r, 4), round(f, 4)
