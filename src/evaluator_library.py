from rouge import Rouge
rouge = Rouge()


def fetchEvaluators(enabledEvaluators):

    EVALUATORS = {
        'rouge': rouge,
    }

    enabledEvaluators = [
        summarizer.lower() for summarizer in enabledEvaluators
    ]

    desiredEvaluators = dict(
        (k, EVALUATORS[k]) for k in enabledEvaluators if k in EVALUATORS
    )

    return desiredEvaluators
