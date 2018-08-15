import os
import codecs

from .EvaluatorLibrary import fetchEvaluators

from tqdm import tqdm

from tools.utils import (
    TemporaryDirectory
)

from tools.logger import Logger
LOGGER = Logger.getInstance()


class EvaluatorSwitch(object):
    def __init__(self, evaluators, tokenizer):
        self.tokenizer = tokenizer
        self.evaluationLibrary = fetchEvaluators(evaluators)
        self.functionMap = {
            'rouge': self._rougeScore,
            'pyrouge': self._pyRouge,
            'meteor': self._meteor,
            'bleu': self._bleu
        }
        self.functionMap = dict(
            (k.lower(), v)
            for k, v in self.functionMap.items()
        )

    def executeAndReportEvaluatorsOnCorpus(self, SRO):
        evaluatorReportsForCorpus = {}
        currSRO = SRO
        for evaluator in self.evaluationLibrary:
            result = self._toggleAndExecuteEvaluator(
                evaluator, currSRO)
            currSRO = currSRO.copy()

            evaluatorReportsForCorpus[evaluator] = result

        return evaluatorReportsForCorpus

    def _toggleAndExecuteEvaluator(self, evaluatorKey, SRO):
        functions = self.functionMap

        if evaluatorKey in functions:
            method = functions[evaluatorKey]
            report = method(SRO)
            return report

        error = '{0}: Is not an available evaluator'.format(evaluatorKey)
        raise ValueError(error)

    def _bleu(self, SRO):
        tokenizer = self.tokenizer
        LOGGER.info('Calculating BLEU Score:')
        bleu = self.evaluationLibrary['bleu']

        readerLength = len(SRO)
        numSamples = 0
        sumScores = 0.0
        for i in tqdm(range(readerLength)):
            hypothesis, references = SRO.readOne()

            hypothesisTokens = tokenizer.word_tokenize(hypothesis)

            referenceTokensLists = [
                tokenizer.word_tokenize(sentence)
                for reference in references
                for sentence in tokenizer.sent_tokenize(reference)
            ]

            scores = bleu(hypothesisTokens, referenceTokensLists)
            bleuScore = scores[0]

            sumScores += bleuScore
            numSamples += 1

        avg = (float(sumScores) * 100 / float(numSamples)) if readerLength \
            else 0.0

        return avg

    def _meteor(self, SRO):
        LOGGER.info('Calculating METEOR Score:')

        meteor = self.evaluationLibrary['meteor']

        readerLength = len(SRO)
        numSamples = 0
        sumScores = 0.0
        for i in tqdm(range(readerLength)):
            hypothesis, references = SRO.readOne()
            score = meteor.score(hypothesis, references)

            sumScores += score
            numSamples += 1

        avg = (float(sumScores) * 100 / float(numSamples)) if readerLength \
            else 0.0

        return avg

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
            'rouge-1': {k: float(sumRouge1[k]) * 100 / float(numSamples)
                        for k in sumRouge1 if numSamples > 0},
            'rouge-2': {k: float(sumRouge2[k]) * 100 / float(numSamples)
                        for k in sumRouge2 if numSamples > 0},
            'rouge-l': {k: float(sumRougel[k]) * 100 / float(numSamples)
                        for k in sumRougel if numSamples > 0}
        }

        return avg

    def _pyRouge(self, SRO):
        LOGGER.info('Calculating pyRouge score:')
        Rouge155 = self.evaluationLibrary['pyrouge']
        output = ''

        readerLength = len(SRO)
        failures = SRO.failedIndicies
        if len(failures) == readerLength:
            # No summaries were successful
            return [
                'The pyRouge score could not be calculated. No'
                ' summaries were succesfully generated.',
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

        return output
