import configparser
import json
import csv
import glob
import os
import codecs
from tools.SRO import SummaryReaderObject
from datetime import datetime
from tqdm import tqdm
from tools.plot import plotTable, plotSystemsCorpusPerMetric
from tools.utils import (
    fileLen,
    createFolderIfNotExists,
    fileExists
)

from collections import defaultdict

from Summarizer.SummarizerLibrary import fetchSummarizers
from Summarizer.SummarizerSwitch import SummarizerSwitch

from Evaluator.EvaluatorSwitch import EvaluatorSwitch

from tools.defaults import (
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
    sys.setdefaultencoding('utf-8')
except NameError:
    pass


class benchmark:
    def __init__(self):
        # Generate Benchmark Tool Folders
        createFolderIfNotExists(
            os.path.join('..', 'data', 'generated_summaries'))

        # Load configuration File
        self.settings = self.initSettings()

        self.dataFolders = self.fetchSettingByKey(
            'data_folders',
            expect_list=True)

        self.subsetsEnabled = False
        # Load Seperators
        textSeperator = self.fetchSeperator('text_seperator')
        self.textSeperator = textSeperator if textSeperator \
            else DEFAULT_TEXT_SEPERATOR

        sentenceSeperator = self.fetchSeperator('sentence_seperator')
        self.sentenceSeperator = sentenceSeperator if sentenceSeperator \
            else DEFAULT_SENTENCE_SEPERATOR

        # load filepaths of samples
        self.corpusFilepaths, self.dataSetToCorpusFilesMap = \
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
        self.summarizerLibrary = fetchSummarizers(summarizers)
        self.summarizerSwitch = SummarizerSwitch(self)

        # load evaluators
        self.evaluatorSwitch = EvaluatorSwitch(evaluators)

        sentenceCount = self.fetchSettingByKey('sentence_count')
        self.sentenceCount = int(sentenceCount) if sentenceCount \
            else DEFAULT_SENTENCE_COUNT

        self.failedIndicies = defaultdict(dict)  # Dict of sampleFilePaths
        # And the indices unsuccesfully summarized, grouped by summarizer
        # This is used for evaluations. If the summarization of a specific
        # set of text fails it will not have a hypothesis. So it cannot be
        # evaluated. This is how we know which indices to skip.
        '''
            {
                'summarizer_name': {
                    'file_path_to_sample': set([0,8])
                                    // set of indices unsuccesfully summarized
                }
            }
        '''
        self.reportTree = defaultdict(dict)
        '''
            {
                'dataset':{
                    'corpus':{
                        'summarizer':{
                            'metric': report
                        }
                    }
                }
            }
        '''
        self.corpusToSummaryMap = defaultdict(dict)
        '''
        Maps to the location of the summary for a given summarizer
        and corpus.
            {
                'summarizer': {
                    'corpusFilePath': 'summaryFilePath'
                }
            }

        '''

    def walkDataCorporaFolders(self):
        dataFolders = self.dataFolders

        corporaFilepaths = []  # Flat List of All avaialble corpora

        dataSetToCorpusFilesMap = {}   # Keeps track of which corpora
        # belong to which datasets
        for folder in dataFolders:
            filesInFolder = glob.glob(
                str(os.path.join(folder, 'samples', '*')))
            corporaFilepaths.extend(filesInFolder)
            dataSetToCorpusFilesMap[folder] = filesInFolder

        return corporaFilepaths, dataSetToCorpusFilesMap

    def initSettings(self):
        settings = configparser.ConfigParser()
        settingsFilepath = './settings.ini'
        settings.read(settingsFilepath)
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
        corpusFilePaths = self.corpusFilepaths
        for filepath in corpusFilePaths:
            self.runSummarizationsForCorpus(filepath, summarizerKey)

    def generateSummaryFilePath(self, corpusFilePath, summarizerKey):
        '''
            input: filepath to corpus and summarizer
            output: filepath for generated summary.
        '''

        corpusFileName = os.path.basename(corpusFilePath)

        summaryFileName = os.path.join(
            '..', 'data', 'generated_summaries',
            '{0}_{1}'.format(
                summarizerKey, corpusFileName)
        )

        return summaryFileName

    def skipSummaryGen(self, generatedSummariesFilePath,
                       corpusFilePath, summarizerKey):
        if fileExists(generatedSummariesFilePath):
            if fileLen(corpusFilePath) == fileLen(generatedSummariesFilePath):
                LOGGER.info(
                    'Skipping Summary Generation. Summaries Aready Exist for '
                    'Corpus: {0} using summarizer: {1} and no failed '
                    'summaries were inferred.'
                    .format(corpusFilePath, summarizerKey))
                return True

        return False

    def runSummarizationsForCorpus(self, corpusFilePath, summarizerKey):
        generatedSummariesFilePath = self.generateSummaryFilePath(
            corpusFilePath, summarizerKey
        )

        # Initializing class maps for failures and summary paths.
        failedIndicies = set()
        self.failedIndicies[summarizerKey][corpusFilePath] = \
            failedIndicies

        self.corpusToSummaryMap[summarizerKey][corpusFilePath] = \
            generatedSummariesFilePath

        if self.skipSummaryGen(generatedSummariesFilePath,
                               corpusFilePath, summarizerKey):
            return

        # Fetching and Running Summarizations
        summarizerSwitch = self.summarizerSwitch

        fileLength = fileLen(corpusFilePath)
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

    def generateCorpusGoldFilePath(self, corpusFilePath):
        '''
            input: path to corpus within a dataset
            output: path to gold(models) for the corpus
        '''
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
        summarizerLibrary = self.summarizerLibrary

        for key in summarizerLibrary:
            self.runSummarizations(key)

        if self.evaluationEnabled:
            self.runEvaluations()
            self.generatePlots()

    def runEvaluations(self):
        corporaReports = {}
        for dataset in self.dataSetToCorpusFilesMap:
            corpusReports = self.evaluateDataSet(dataset)
            corporaReports[dataset] = corpusReports

        self.reportTree = corporaReports

    def evaluateDataSet(self, dataset):
        corpusFilePaths = self.dataSetToCorpusFilesMap[dataset]
        corpusReports = {}
        for corpus in corpusFilePaths:
            report = self.evaluateCorpusPerSummarizer(corpus)
            corpusReports[corpus] = report
        return corpusReports

    def evaluateCorpusPerSummarizer(self, corpusFilepath):
        goldPath = self.generateCorpusGoldFilePath(corpusFilepath)

        summarizerReports = {}
        for summarizerKey in self.summarizers:
            LOGGER.info(
                'Evaluating Results for Corpus: %s using summarizer: %s',
                corpusFilepath,
                summarizerKey
            )

            summaryPath = self.\
                corpusToSummaryMap[summarizerKey.lower()][corpusFilepath]

            failedIndicies = self.\
                failedIndicies[summarizerKey.lower()][corpusFilepath]

            SRO = SummaryReaderObject(
                summaryPath, goldPath, failedIndicies=failedIndicies)

            corpusReport = ''
            corpusReport = self.evaluatorSwitch\
                .executeAndReportEvaluatorsOnCorpus(SRO)
            summarizerReports[summarizerKey] = corpusReport

        return summarizerReports

    def writeToCSV(self, csvList):
        resultsPath = os.path.join('..', 'results')
        createFolderIfNotExists(resultsPath)

        currDatetime = str(datetime.now())
        pathToResults = os.path.join(
            resultsPath,
            "results_{0}.csv".format(
                currDatetime
            )
        )
        with codecs.open(pathToResults, "w") as f:
            writer = csv.writer(f)
            writer.writerows(csvList)
        return pathToResults

    def generatePlots(self):
        #  self.plotReport()
        reportTree = self.reportTree
        summarizers = self.summarizers
        metrics = self.evaluators
        plotSystemsCorpusPerMetric(summarizers, metrics, reportTree)
        return

    def plotReport(self):
        '''
        {
            'dataset':{
                'corpus':{
                    'summarizer':{
                        'metric': report
                    }
                }
            }
        }
        '''
        for dataset in self.reportTree:
            corporaReportMap = self.reportTree[dataset]
            self.plotReportPerCorpora(corporaReportMap)

    def plotReportPerCorpora(self, corporaReportMap):
        for corpus in corporaReportMap:
            corpusReportMap = corporaReportMap[corpus]
            self.plotReportPerCorpus(corpusReportMap)

    def plotReportPerCorpus(self, corpusReportMap):
        csvList = [['Summarizer']]
        evaluators = self.evaluators
        evaluators.sort()
        csvList[0].extend(evaluators)

        for summarizer in corpusReportMap:
            summarizerReportMap = corpusReportMap[summarizer]
            csvLine = self.summarizerReportMapToCSVFormat(
                summarizer,
                summarizerReportMap)
            csvList.append(csvLine)

        pathToCSV = self.writeToCSV(csvList)
        plotTable(pathToCSV)

    def summarizerReportMapToCSVFormat(self, summarizer, summarizerReportMap):
        evaluators = self.evaluators
        evaluators.sort()

        csvLineList = [summarizer]
        for evaluator in evaluators:
            metric = evaluator.lower()
            metricResult = summarizerReportMap[metric]
            csvLineList.append(metricResult)
        return csvLineList


benchmarkInstance = benchmark()
benchmarkInstance.runBenchmarking()
