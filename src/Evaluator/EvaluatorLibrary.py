from rouge import Rouge
from pyrouge import Rouge155
from .evaluator_source_files.Meteor.Meteor import Meteor


def fetchEvaluators(enabledEvaluators):
    '''
        input: list of evaluator keys
        output: dict(
                    evaluatorKey: evaluatorMethod
                                 (None if no method is specified))
        purpose: Onload of evaluator switch this function is called
        before hand to prevent cluttering the file with library
        imports. The output dictionary can be interfaced to
        fetch the metric function desired.
    '''

    EVALUATORS = {
        'rouge': Rouge(),
        'pyrouge': Rouge155,
        'meteor': Meteor()
    }

    enabledEvaluators = [
        summarizer.lower() for summarizer in enabledEvaluators
    ]

    desiredEvaluators = dict(
        (k, EVALUATORS[k])
        if k in EVALUATORS else (k, None)
        for k in enabledEvaluators
    )

    return desiredEvaluators
