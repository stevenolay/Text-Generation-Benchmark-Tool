import os
import codecs

from EvaluatorLibrary import fetchEvaluators

from tqdm import tqdm

from utils import (
    TemporaryDirectory,
    fileLen,
    fileLenOpen
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
            'rouge': self.rougeScore,
            'pyrouge': self.pyRouge,
            'meteor': self.meteor
        }

    def executeAndReportEvaluatorsOnCorpus(self, SRO):
        evaluatorReportsForCorpus = []
        for evaluator in self.evaluationLibrary:
            report = self.toggleAndExecuteEvaluator(
                evaluator, SRO.copy())

            evaluatorReportsForCorpus.extend(report)

        return ''.join(evaluatorReportsForCorpus)

    def toggleAndExecuteEvaluator(self, evaluatorKey, SRO):
        functions = self.functionMap

        if evaluatorKey in functions:
            method = functions[evaluatorKey]
            report = method(SRO)
            return report

        error = '{0}: Is not an available evaluator'.format(evaluatorKey)
        raise ValueError(error)

    def meteor(self, SRO):
        LOGGER.info('Calculating Meteor Score:')

        meteor = self.evaluationLibrary['meteor']

        readerLength = SRO.length
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

    def rougeScore(self, SRO):
        LOGGER.info('Calculating Rouge Score:')

        rouge = self.evaluationLibrary['rouge']

        sumRouge1 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRouge2 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRougel = {'r': 0.0, 'p': 0.0, 'f': 0.0}

        readerLength = SRO.length
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

    def pyRouge(self, summaries, goldExamples, failures):
        LOGGER.info('Calculating pyRouge score:')
        Rouge155 = self.evaluationLibrary['pyrouge']
        output = ''

        goldFileLength = fileLen(goldExamples.name)

        if len(failures) == goldFileLength:
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

            for i in tqdm(range(goldFileLength)):
                goldExample = goldExamples.readline()
                if i in failures:
                    # If the summary failed we skip to the next gold example
                    continue
                summary = summaries.readline()  # Only proceed the summary read
                # if the current sample count did not fail.

                summary_fn = '%i.txt' % i
                gold_fn = '%i.%i.txt' % (i, 0)
                with codecs.open(os.path.join(
                    model_dir, gold_fn), 'w', 'utf-8'
                ) as f:
                    f.write(goldExample)

                with codecs.open(os.path.join(
                    system_dir, summary_fn), 'w', 'utf-8'
                ) as f:
                    f.write(summary)

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
