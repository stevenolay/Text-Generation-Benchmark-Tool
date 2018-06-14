from rouge import Rouge
rouge = Rouge()

from pyrouge import Rouge155


def fetchEvaluators(enabledEvaluators):

    EVALUATORS = {
        'rouge': rouge,
        'pyrouge': Rouge155
    }

    enabledEvaluators = [
        summarizer.lower() for summarizer in enabledEvaluators
    ]

    desiredEvaluators = dict(
        (k, EVALUATORS[k]) for k in enabledEvaluators if k in EVALUATORS
    )

    return desiredEvaluators
