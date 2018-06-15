import configparser
import json
import glob
import os
import codecs

import tempfile
from tqdm import tqdm

from summarizer_library import fetchSummarizers
from evaluator_library import fetchEvaluators

from collections import defaultdict

from mappings import (
    SUPPORTED_EVAL_SYSTEMS,
    SUPPORTED_TOKENIZERS,
    SUPPORTED_SUMMARIZERS,
    DEFAULT_TOKENIZER,
    DEFAULT_TEXT_SEPERATOR,
    DEFAULT_SENTENCE_SEPERATOR,
    DEFAULT_SENTENCE_COUNT
)

import logging
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT,
                    level=logging.DEBUG)
LOGGER = logging.getLogger()


class benchmark:
    def __init__(self):
        # Load configuration File
        self.settings = self.initSettings()

        self.data_folders = self.fetchSettingByKey(
            'data_folders',
            expect_list=True
        )
        self.subsetsEnabled = False
        # Load Seperators
        textSeperator = self.fetchSeperator('text_seperator')
        self.textSeperator = textSeperator if textSeperator \
            else DEFAULT_TEXT_SEPERATOR

        sentenceSeperator = self.fetchSeperator('sentence_seperator')
        self.sentenceSeperator = sentenceSeperator if sentenceSeperator \
            else DEFAULT_SENTENCE_SEPERATOR

        # load filepaths of samples
        self.corpus_filepaths, self.dataSetToCorpusFilesMap = \
            self.walkDataCorporaFolders()

        # Load Summarizers
        summarizers = self.fetchSettingByKey(
            'summarizers',
            expect_list=True)

        self.validateOptions(summarizers, SUPPORTED_SUMMARIZERS)
        self.summarizers = summarizers
        # Load Evaluatos
        evaluators = self.fetchSettingByKey(
            'evaluation_systems',
            expect_list=True)

        self.validateOptions(evaluators, SUPPORTED_EVAL_SYSTEMS)
        self.evaluators = evaluators

        # Load Tokenizer
        tokenizer = self.fetchSettingByKey('tokenizer')
        self.validateOption(tokenizer, SUPPORTED_TOKENIZERS)
        self.tokenizer = tokenizer if tokenizer else DEFAULT_TOKENIZER

        # Load Evaluation Systems
        evaluationSystems = self.fetchSettingByKey(
            'evaluation_systems',
            expect_list=True)

        self.validateOptions(evaluationSystems, SUPPORTED_EVAL_SYSTEMS)
        self.evaluationSystems = evaluationSystems

        # Load States
        evaluationEnabled = self.fetchSettingByKey('evaluation_enabled')
        evaluationEnabled = self.evaluateBoolean(evaluationEnabled)
        self.evaluationEnabled = evaluationEnabled if evaluationEnabled \
            else False

        preTokenized = self.fetchSettingByKey('pre_tokenized')
        preTokenized = self.evaluateBoolean(preTokenized)
        self.preTokenized = preTokenized if preTokenized else False

        # load summarizers
        self.summarizer_library = fetchSummarizers(summarizers)
        self.summarizerSwitch = SummarizerSwitch(self)

        # load evaluators
        self.evaluation_library = fetchEvaluators(evaluators)
        self.evaluatorSwitch = EvaluateSwitch(self)

        sentenceCount = self.fetchSettingByKey('sentence_count')
        self.sentenceCount = int(sentenceCount) if sentenceCount \
            else DEFAULT_SENTENCE_COUNT

        self.failedIndicies = defaultdict(dict)  # Dict of sampleFilePaths
        # And the indices unsuccesfully summarized, grouped by summarizer
        # This is used for evaluations. If the summarization of a specific
        # set of text fails it will not have an hypothesis. So it cannot be
        # evaluated. This is how we know which indices to skip.
        '''
            {
                'summarizer_name': {
                    'file_path_to_sample': set([0,8])
                                    // set of indices unsuccesfully summarized
                }
            }
        '''
        self.corpusToSummaryMap = defaultdict(dict)

    def walkDataCorporaFolders(self):
        dataFolders = self.data_folders

        corpora_filepaths = []  # Flat List of All avaialble corpora

        dataSetToCorpusFilesMap = {}   # Keeps track of which samples
        # belong to which datasets
        for folder in dataFolders:
            filesInFolder = glob.glob(str(os.path.join(folder, 'samples/*')))
            corpora_filepaths.extend(filesInFolder)
            dataSetToCorpusFilesMap[folder] = filesInFolder

        return corpora_filepaths, dataSetToCorpusFilesMap

    def initSettings(self):
        settings = configparser.ConfigParser()
        settings_filepath = 'settings.ini'
        settings.read(settings_filepath)
        return settings

    def validateOption(self, suppliedOption, validOptionsSet):
        suppliedOption = suppliedOption.lower()
        if suppliedOption not in validOptionsSet:
            error = [
                suppliedOption,
                ': Is not a supported option. Choose from: ',
                ', '.join(list(validOptionsSet))
            ]
            raise ValueError(''.join(error))

    def validateOptions(self, userInputOptions, validOptionsSet):
        for option in userInputOptions:
            self.validateOption(option, validOptionsSet)
        return

    def evaluateBoolean(self, booleanText):
        if not booleanText:
            return False

        booleanTextLower = booleanText.lower()
        boolean = json.loads(booleanTextLower)

        if boolean not in set([True, False]):
            error = [
                booleanText,
                ': This setting is invalid. Expected True or False'
            ]
            raise ValueError(''.join(error))

        return boolean

    def fetchSettingByKey(self, key, **kwargs):
        section = 'general'
        if 'section' in kwargs:
            section = kwargs['section']

        expectList = False
        if 'expect_list' in kwargs:
            expectList = kwargs['expect_list']

        settings = self.settings

        if expectList:
            targetedSetting = settings.get(section, key)
            targetedSettingList = targetedSetting.replace(' ', '').split(',')
            return targetedSettingList
        else:
            targetedSetting = settings.get(section, key)
            return targetedSetting

    def fetchSeperator(self, key):
        settings = self.settings
        try:
            seperator = settings.get('general', key)
        except configparser.NoOptionError:
            return None

        decodedSeperator = bytes(seperator, 'utf-8').decode('unicode_escape')

        return decodedSeperator

    def runSummarizations(self, summarizerKey):
        corpusFilePaths = self.corpus_filepaths
        for filepath in corpusFilePaths:
            self.runSummarizationsForCorpus(filepath, summarizerKey)

    def generateSummaryFilePath(self, corpusFilePath, summarizerKey):

        corpusFileName = os.path.basename(corpusFilePath)

        summaryFileName = os.path.join(
            '../data/generated_summaries/',
            '{0}_{1}'.format(
                summarizerKey, corpusFileName)
        )

        return summaryFileName

    def runSummarizationsForCorpus(self, corpusFilePath, summarizerKey):
        generatedSummariesFilePath = self.generateSummaryFilePath(
            corpusFilePath, summarizerKey
        )

        summarizerSwitch = self.summarizerSwitch

        failedIndicies = set()
        fileLength = file_len(corpusFilePath)
        results = codecs.open(generatedSummariesFilePath, 'w', 'utf-8')
        samples = codecs.open(corpusFilePath, 'rb+', 'utf-8')

        LOGGER.info(
            'Generating summaries for corpus: {0} using summarizer: {1}'
            .format(corpusFilePath, summarizerKey))

        for index, text in tqdm(enumerate(samples), total=fileLength):
            generatedSummary = summarizerSwitch.toggleAndExecuteSummarizer(
                summarizerKey, text)

            if not generatedSummary:
                failedIndicies.add(index)
                if index == fileLength - 1:  # Delete the extra \n(newline)
                    results.seek(-1, os.SEEK_END)
                    results.truncate()
                continue

            if index < (fileLength - 1):
                results.write('{0}\n'.format(generatedSummary))
            else:
                results.write('{0}'.format(generatedSummary))

        samples.close()  # Close the corpora file.
        results.close()  # Close the results file.

        self.failedIndicies[summarizerKey][corpusFilePath] = \
            failedIndicies

        self.corpusToSummaryMap[summarizerKey][corpusFilePath] = \
            generatedSummariesFilePath

    def generateCorpusGoldFilePath(self, corpusFilePath):
        corpusFileFolder, corpusFileName = os.path.split(corpusFilePath)
        dataSetFileFolder, subDir = os.path.split(corpusFileFolder)
        fileName, ext = os.path.splitext(corpusFileName)

        corpusGoldFilePath = os.path.join(
            dataSetFileFolder,
            'gold',
            '{0}_gold{1}'.format(
                fileName, ext)
        )

        return corpusGoldFilePath

    def runBenchmarking(self):
        summarizerLibrary = self.summarizer_library

        for key in summarizerLibrary:
            self.runSummarizations(key)

        if self.evaluationEnabled:
            self.runEvaluations()

    def runEvaluations(self):
        for dataSet in self.dataSetToCorpusFilesMap:
            self.evaluateDataSet(dataSet)

    def evaluateDataSet(self, dataset):
        corpusFilePaths = self.dataSetToCorpusFilesMap[dataset]
        corpusReports = ['Report for Dataset:\t{0}\n'.format(dataset)]
        for corpus in corpusFilePaths:
            corpusReports.append(
                '\n\tReporting for Corpus: {0}\n'.format(corpus)
            )
            report = self.evaluateCorpusPerSummarizer(corpus)
            corpusReports.extend(['\n\t\t', report])
        print(''.join(corpusReports))

    def evaluateCorpusPerSummarizer(self, corpusFilepath):
        goldPath = self.generateCorpusGoldFilePath(corpusFilepath)

        summarizerReports = []
        for summarizerKey in self.summarizers:
            LOGGER.info(
                'Evaluating Results for Corpus: %s using summarizer: %s',
                corpusFilepath,
                summarizerKey
            )

            summarizerReports.append(
                '\n\t\tSummarizer: {0}\n\t\t\t'.format(summarizerKey)
            )

            summaryPath = self.\
                corpusToSummaryMap[summarizerKey.lower()][corpusFilepath]
            summaries = codecs.open(summaryPath, 'r', 'utf-8')

            corpusReport = ''
            '''
            if self.subsetsEnabled:
                self.generateGoldSubset(
                    goldPath, corpusFilepath, summarizerKey)

                goldSubsetFilePath = self.generateGoldSubsetFilePath(
                    corpusFilepath, summarizerKey)

                goldSubset = codecs.open(goldSubsetFilePath, 'r', 'utf-8')

                failedIndicies = set()  # Set the failedIndices to an empty set
                # no need to skip any summaries as a subset was fully
                # constructed.
                corpusReport = self.evaluatorSwitch\
                    .executeAndReportEvaluatorsOnCorpus(
                        summaries, goldSubset, failedIndicies
                    )
                goldSubset.close()
            else:
            '''
            goldExamples = codecs.open(goldPath, 'r', 'utf-8')
            failedIndicies = self.\
                failedIndicies[summarizerKey.lower()][corpusFilepath]
            corpusReport = self.evaluatorSwitch\
                .executeAndReportEvaluatorsOnCorpus(
                    summaries, goldExamples, failedIndicies
                )
            goldExamples.close()

            summaries.close()
            summarizerReports.append(corpusReport)

        return ''.join(summarizerReports)

    def generateGoldSubset(self, goldPath, corpusFilepath, summarizerKey):
        LOGGER.info(
            'Generating Goldsubset for Corpus: %s using summarizer: %s',
            corpusFilepath,
            summarizerKey.lower()
        )

        failedIndicies = self.\
            failedIndicies[summarizerKey.lower()][corpusFilepath]

        goldSubsetFilePath = self.generateGoldSubsetFilePath(
            corpusFilepath, summarizerKey)

        goldSet = codecs.open(goldPath, 'r', 'utf-8')
        fileLength = file_len(goldPath)
        goldSubset = codecs.open(goldSubsetFilePath, 'w', 'utf-8')

        for index, text in tqdm(enumerate(goldSet), total=fileLength):

            if index in failedIndicies:
                if index == fileLength - 1:  # Delete the extra \n(newline)
                    goldSubset.seek(-1, os.SEEK_END)
                    goldSubset.truncate()
                continue

            if index < (fileLength - 1):
                goldSubset.write('{0}'.format(text))
            else:
                goldSubset.write('{0}'.format(text))
        goldSet.close()
        goldSubset.close()

    def generateGoldSubsetFilePath(self, corpusFilepath, summarizerKey):
        corpusFileName = os.path.basename(corpusFilepath)
        fileName, ext = os.path.splitext(corpusFileName)

        goldSubsetFilePath = os.path.join(
            '../data/gold_subsets/',
            '{0}_{1}_gold{2}'.format(
                summarizerKey.lower(), fileName, ext)
        )
        return goldSubsetFilePath


class EvaluateSwitch(object):
    def __init__(self, benchmarkInstance):
        self.evaluation_library = benchmarkInstance.evaluation_library
        self.functionMap = {
            'rouge': self.rougeScore,
            'pyrouge': self.pyRouge
        }

    def executeAndReportEvaluatorsOnCorpus(self, summaries, goldExamples,
                                           failures):
        evaluatorReportsForCorpus = []
        for evaluator in self.evaluation_library:
            report = self.toggleAndExecuteEvaluator(
                evaluator, summaries, goldExamples, failures)
            summaries.seek(0)
            goldExamples.seek(0)
            evaluatorReportsForCorpus.extend(report)
        return ''.join(evaluatorReportsForCorpus)

    def toggleAndExecuteEvaluator(self, evaluatorKey,
                                  summaries, goldExamples, failures):
        functions = self.functionMap

        if evaluatorKey in functions:
            method = functions[evaluatorKey]
            report = method(summaries, goldExamples, failures)
            return report

        error = '{0}: Is not an available evaluator'.format(evaluatorKey)
        raise ValueError(error)

    def rougeScore(self, summaries, goldExamples, failures):
        LOGGER.info('Calculating Rouge Score:')

        rouge = self.evaluation_library['rouge']

        sumRouge1 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRouge2 = {'r': 0.0, 'p': 0.0, 'f': 0.0}
        sumRougel = {'r': 0.0, 'p': 0.0, 'f': 0.0}

        goldFileLength = file_len_open(goldExamples)
        numSamples = 0
        for i in tqdm(range(goldFileLength)):
            goldExample = goldExamples.readline()
            if numSamples in failures:
                # If the summary failed we skip to the next gold example
                numSamples += 1
                continue
            summary = summaries.readline()  # Only proceed the summary read
            # if the current sample count did not fail.

            sampleHypothesisText = summary
            goldText = goldExample

            score = rouge.get_scores(sampleHypothesisText, goldText)[0]
            sumRouge1 = {k: sumRouge1[k] + score['rouge-1'][k]
                         for k in sumRouge1}
            sumRouge2 = {k: sumRouge2[k] + score['rouge-2'][k]
                         for k in sumRouge2}
            sumRougel = {k: sumRougel[k] + score['rouge-l'][k]
                         for k in sumRougel}

            numSamples += 1

        avg = {
            'rouge-1': {k: sumRouge1[k] / float(numSamples)
                        for k in sumRouge1 if numSamples > 0},
            'rouge-2': {k: sumRouge2[k] / float(numSamples)
                        for k in sumRouge2 if numSamples > 0},
            'rouge-l': {k: sumRougel[k] / float(numSamples)
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
        Rouge155 = self.evaluation_library['pyrouge']
        output = ''
        outputDict = {}
        with tempfile.TemporaryDirectory() as temp_dir:
            system_dir = os.path.join(temp_dir, 'system')
            model_dir = os.path.join(temp_dir, 'model')
            os.makedirs(system_dir)
            os.makedirs(model_dir)
            goldFileLength = file_len(goldExamples.name)
            for i in tqdm(range(goldFileLength)):
                goldExample = goldExamples.readline()
                if i in failures:
                    # If the summary failed we skip to the next gold example
                    continue
                summary = summaries.readline()  # Only proceed the summary read
                # if the current sample count did not fail.

                summary_fn = '%i.txt' % i
                gold_fn = '%i.%i.txt' % (i, 0)
                with codecs.open(os.path.join(model_dir, gold_fn), 'w') as f:
                    f.write(goldExample)
                with codecs.open(os.path.join(system_dir, summary_fn), 'w') as f:
                    f.write(summary)

            '''
            rouge_args = [
                '-c', 95,
                '-U',
                '-r', 1,
                '-n', 2,
                '-a',
            ]
            '''
            # args_str = ' '.join(map(str, rouge_args))
            # rouge = Rouge155(rouge_args=args_str)

            rouge = Rouge155()
            rouge.system_dir = system_dir
            rouge.model_dir = model_dir
            rouge.system_filename_pattern = '(\d+).txt'
            rouge.model_filename_pattern = '#ID#.\d+.txt'

            output = rouge.convert_and_evaluate()
            outputDict = rouge.output_to_dict(output)

        report = [
            '\n\t\t\tThis is the result of the pyRogue Score:\n\t\t\t\t',
            str(output.replace('\n', '\n\t\t\t\t')),
            '\n'
        ]

        return report


class SummarizerSwitch(object):
    def __init__(self, benchmarkInstance):
        self.benchmark = benchmarkInstance
        self.summarizer_library = benchmarkInstance.summarizer_library
        self.functionMap = {
            'smmrre': self.smmrre,
            'sumy': self.sumy
        }

    def joinTokenizedSentences(self, text):
        benchmark = self.benchmark
        sentenceSeperator = benchmark.sentenceSeperator
        newText = text.replace(sentenceSeperator, '')
        return newText

    def splitTokenizedSentences(self, text):
        benchmark = self.benchmark
        sentenceSeperator = benchmark.sentenceSeperator
        newText = text.split(sentenceSeperator)
        return newText

    def toggleAndExecuteSummarizer(self, summarizerKey, text):
        functions = self.functionMap

        if summarizerKey in functions:
            method = functions[summarizerKey]
            return method(text)  # Method should return a summary
        error = '{0}: Is not an available summarizer'.format(summarizerKey)
        raise ValueError(error)

    def smmrre(self, text):
        benchmark = self.benchmark
        numSentences = benchmark.sentenceCount

        if benchmark.preTokenized:
            # smmrRE expects text to not be pretokenized
            text = self.joinTokenizedSentences(text)

        smmrREClass = self.summarizer_library['smmrre']
        smmrRE = smmrREClass(text)

        summary = smmrRE.summarize(numSentences)

        return summary

    def sumy(self, text):
        benchmark = self.benchmark
        numSentences = benchmark.sentenceCount

        if benchmark.preTokenized:
            # sumy has it's own tokenizer
            text = self.joinTokenizedSentences(text)

        sumyClass = self.summarizer_library['sumy']
        sumy = sumyClass(text)

        summary = sumy.summarize(numSentences, 'english')

        return summary


def copyFile(src, dst):
    with codecs.open(src, 'r', 'utf-8') as f:
        with codecs.open(dst, 'w', 'utf-8') as f1:
            for line in f:
                f1.write(line)


def file_len_open(f):
    i = -1
    for i, l in enumerate(f):
        pass
    f.seek(0)
    return i + 1


def file_len(fname):
    '''
        Calculates the line count for a given file line by line to prevent
         loading lines into memory all at once.
        SOURCE:
            https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
    '''
    i = -1
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
        f.seek(0)
    return i + 1


benchmarkInstance = benchmark()
benchmarkInstance.runBenchmarking()
