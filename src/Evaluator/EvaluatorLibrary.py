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

    desiredEvaluators = dict(
        (k.lower(), EVALUATORS[k.lower()])
        if k.lower() in EVALUATORS else (k, None)
        for k in enabledEvaluators
    )# Only lowercase keys in the evaluators list. As users may opt out of
     # using this to assist to load in libraries for their metrics.

    return desiredEvaluators
