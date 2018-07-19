import os
import codecs

from .EvaluatorLibrary import fetchEvaluators

from tqdm import tqdm

from utils import (
    TemporaryDirectory,
    fileLen
)

import logging

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT,
                    level=logging.DEBUG)
LOGGER = logging.getLogger()


class EvaluatorSwitch(object):
    def __init__(self, evaluators):
        self.evaluationLibrary = fetchEvaluators(evaluators)
        self.functionMap = {
            'rouge': self._rougeScore,
            'pyrouge': self._pyRouge,
            'meteor': self._meteor
        }

    def executeAndReportEvaluatorsOnCorpus(self, SRO):
        assert str(type(SRO)) == "<class 'SRO.SummaryReaderObject'>"

        evaluatorReportsForCorpus = []
        currSRO = SRO
        for evaluator in self.evaluationLibrary:
            report = self._toggleAndExecuteEvaluator(
                evaluator, currSRO)
            currSRO = currSRO.copy()

            evaluatorReportsForCorpus.extend(report)

        return ''.join(evaluatorReportsForCorpus)

    def _toggleAndExecuteEvaluator(self, evaluatorKey, SRO):
        functions = self.functionMap

        if evaluatorKey in functions:
            method = functions[evaluatorKey]
            report = method(SRO)
            return report

        error = '{0}: Is not an available evaluator'.format(evaluatorKey)
        raise ValueError(error)

    def _meteor(self, SRO):
        LOGGER.info('Calculating Meteor Score:')

        meteor = self.evaluationLibrary['meteor']

        readerLength = len(SRO)
        numSamples = 0
        sumScores = 0.0
        for i in tqdm(range(readerLength)):
            hypothesis, references = SRO.readOne()
            score = meteor.score(hypothesis, references)

            sumScores += score
            numSamples += 1

        avg = float(sumScores) / float(numSamples)

        report = [
            '\n\t\t\tThis is the result of the Meteor Score:\n\t\t\t\t',
            str(avg),
            '\n'
        ]

        return report

    def _rougeScore(self, SRO):
        LOGGER.info('Calculating Rouge Score:')

        rouge = self.evaluationLibrary['rouge']

        sumRouge1 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRouge2 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRougel = {'r': 0.0, 'p': 0.0, 'f': 0.0}

        readerLength = len(SRO)
        numSamples = 0
        for i in tqdm(range(readerLength)):
            hypothesis, references = SRO.readOne()
            for reference in references:
                score = rouge.get_scores(hypothesis, reference)[0]
                sumRouge1 = {k: sumRouge1[k] + score['rouge-1'][k]
                             for k in sumRouge1}
                sumRouge2 = {k: sumRouge2[k] + score['rouge-2'][k]
                             for k in sumRouge2}
                sumRougel = {k: sumRougel[k] + score['rouge-l'][k]
                             for k in sumRougel}

                numSamples += 1

        avg = {
            'rouge-1': {k: float(sumRouge1[k]) / float(numSamples)
                        for k in sumRouge1 if numSamples > 0},
            'rouge-2': {k: float(sumRouge2[k]) / float(numSamples)
                        for k in sumRouge2 if numSamples > 0},
            'rouge-l': {k: float(sumRougel[k]) / float(numSamples)
                        for k in sumRougel if numSamples > 0}
        }

        report = [
            '\n\t\t\tThis is the result of the Rogue Score:\n\t\t\t\t',
            str(avg),
            '\n'
        ]

        return report

    def _pyRouge(self, SRO):
        LOGGER.info('Calculating pyRouge score:')
        Rouge155 = self.evaluationLibrary['pyrouge']
        output = ''

        readerLength = len(SRO)
        failures = SRO.failedIndicies
        if len(failures) == readerLength:
            # No summaries were successful
            return [
                '\n\t\t\tThe pyRouge score could not be calculated. No'
                ' summaries were succesfully generated:\n\t\t\t\t',
            ]

        with TemporaryDirectory() as temp_dir:
            system_dir = os.path.join(temp_dir, 'system')
            model_dir = os.path.join(temp_dir, 'model')
            os.makedirs(system_dir)
            os.makedirs(model_dir)

            for i in tqdm(range(readerLength)):
                hypothesis, references = SRO.readOne()

                hypothesis_fn = '%i.txt' % i
                for j, reference in enumerate(references):
                    ref_fn = '%i.%i.txt' % (i, j)
                    with codecs.open(os.path.join(
                        model_dir, ref_fn), 'w', 'utf-8'
                    ) as f:
                        f.write(reference)

                    with codecs.open(os.path.join(
                        system_dir, hypothesis_fn), 'w', 'utf-8'
                    ) as f:
                        f.write(hypothesis)

            rouge = Rouge155()

            rouge.system_dir = system_dir
            rouge.model_dir = model_dir
            rouge.system_filename_pattern = '(\d+).txt'
            rouge.model_filename_pattern = '#ID#.\d+.txt'

            output = rouge.convert_and_evaluate()

        report = [
            '\n\t\t\tThis is the result of the pyRogue Score:\n\t\t\t\t',
            str(output.replace('\n', '\n\t\t\t\t')),
            '\n'
        ]

        return report
