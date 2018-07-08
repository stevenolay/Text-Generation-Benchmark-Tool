import configparser
import json
import glob
import os
import codecs


from tqdm import tqdm
from utils import (
    file_len,
    create_folder_if_not_exists
)
from summarizer_library import fetchSummarizers
from evaluator_library import fetchEvaluators

from collections import defaultdict

from SummarizerSwitch import SummarizerSwitch
from EvaluatorSwitch import EvaluatorSwitch

from mappings import (
    SUPPORTED_EVAL_SYSTEMS,
    SUPPORTED_TOKENIZERS,
    SUPPORTED_SUMMARIZERS,
    DEFAULT_TOKENIZER,
    DEFAULT_TEXT_SEPERATOR,
    DEFAULT_SENTENCE_SEPERATOR,
    DEFAULT_SENTENCE_COUNT
)

from duc_parser import OrderDUC2004

import logging

FORMAT = '%(asctime)-15s %(message)s'
LOG_FILENAME = 'allLogs.log'
logging.basicConfig(format=FORMAT,
                    level=logging.DEBUG,
                    filename=LOG_FILENAME)
LOGGER = logging.getLogger()

dirname, filename = os.path.split(os.path.abspath(__file__))
os.chdir(dirname)  # Change the current working directory
# to the directory of the script. All file loads are relative
# to the script directory.

try:  # Used for Python 2 compatibility
    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")
except NameError:
    pass


class benchmark:
    def __init__(self):
        # Load configuration File
        self.settings = self.initSettings()

        self.data_folders = self.fetchSettingByKey(
            'data_folders',
            expect_list=True
        )

        ducEnabled = self.fetchSettingByKey('DUC')
        evaluationEnabled = self.evaluateBoolean(ducEnabled)
        self.ducEnabled = ducEnabled if ducEnabled \
            else False

        if self.ducEnabled:
            OrderDUC2004()
            self.data_folders.append('../data/DUC')

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

        self.evaluatorSwitch = EvaluatorSwitch(self)

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
            filesInFolder = glob.glob(
                str(os.path.join(folder, 'samples', '*')))
            corpora_filepaths.extend(filesInFolder)
            dataSetToCorpusFilesMap[folder] = filesInFolder

        return corpora_filepaths, dataSetToCorpusFilesMap

    def initSettings(self):
        settings = configparser.ConfigParser()
        settings_filepath = './settings.ini'
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

        decodedSeperator = seperator
        try:  # Python 3
            decodedSeperator = bytes(seperator, 'utf-8') \
                .decode('unicode_escape')
        except TypeError:  # Python 2
            decodedSeperator = bytes(seperator) \
                .decode('unicode_escape')

        return decodedSeperator

    def runSummarizations(self, summarizerKey):
        corpusFilePaths = self.corpus_filepaths
        for filepath in corpusFilePaths:
            self.runSummarizationsForCorpus(filepath, summarizerKey)

    def generateSummaryFilePath(self, corpusFilePath, summarizerKey):

        corpusFileName = os.path.basename(corpusFilePath)

        summaryFileName = os.path.join(
            '..', 'data', 'generated_summaries',
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
                    try:
                        results.seek(-1, os.SEEK_END)
                        results.truncate()
                    except IOError:  # Fails if file is completely empty
                        pass
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
        corporaReports = []
        for dataSet in self.dataSetToCorpusFilesMap:
            corpusReports = self.evaluateDataSet(dataSet)
            corporaReports.extend(corpusReports)
        print(''.join(corporaReports))

    def evaluateDataSet(self, dataset):
        corpusFilePaths = self.dataSetToCorpusFilesMap[dataset]
        corpusReports = ['\nReport for Dataset:\t{0}\n'.format(dataset)]
        for corpus in corpusFilePaths:
            corpusReports.append(
                '\n\tReporting for Corpus: {0}'.format(corpus)
            )
            report = self.evaluateCorpusPerSummarizer(corpus)
            corpusReports.extend(['\n\t\t', report])
        return corpusReports

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
            '..', 'data', 'gold_subsets',
            '{0}_{1}_gold{2}'.format(
                summarizerKey.lower(), fileName, ext)
        )
        return goldSubsetFilePath


create_folder_if_not_exists(os.path.join('..', 'data', 'generated_summaries'))

benchmarkInstance = benchmark()
benchmarkInstance.runBenchmarking()
