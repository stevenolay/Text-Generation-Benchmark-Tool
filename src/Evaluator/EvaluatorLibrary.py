from rouge import Rouge
from pyrouge import Rouge155
from .evaluator_source_files.Meteor.Meteor import Meteor


def fetchEvaluators(enabledEvaluators):

    EVALUATORS = {
        'rouge': Rouge(),
        'pyrouge': Rouge155,
        'meteor': Meteor()
    }

    enabledEvaluators = [
        summarizer.lower() for summarizer in enabledEvaluators
    ]

    desiredEvaluators = dict(
        (k, EVALUATORS[k]) for k in enabledEvaluators if k in EVALUATORS
    )

    return desiredEvaluators
