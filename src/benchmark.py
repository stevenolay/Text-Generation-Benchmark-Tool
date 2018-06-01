import configparser
import json
import glob
import os

import pandas as pd

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


class benchmark:
    def __init__(self):
        # Load configuration File
        self.settings = self.initSettings()

        self.data_folders = self.fetchSettingByKey(
            'data_folders',
            expect_list=True
        )

        # Load Seperators
        textSeperator = self.fetchSeperator('text_seperator')
        self.textSeperator = textSeperator if textSeperator \
            else DEFAULT_TEXT_SEPERATOR

        sentenceSeperator = self.fetchSeperator('sentence_seperator')
        self.sentenceSeperator = sentenceSeperator if sentenceSeperator \
            else DEFAULT_SENTENCE_SEPERATOR

        # load filepaths of samples
        self.sample_filepaths, self.dataSetToSampleFilesMap = \
            self.walkDataSampleFolders()

        self.dataFrames = self.cacheDataFramesForSamples()
        self.goldDataFrames = self.cacheDataFramesForGoldSamples()

        # Load Summarizers
        summarizers = self.fetchSettingByKey(
            'summarizers',
            expect_list=True
        )

        self.validateOptions(summarizers, SUPPORTED_SUMMARIZERS)
        self.summarizers = summarizers
        # Load Evaluatos
        evaluators = self.fetchSettingByKey(
            'evaluation_systems',
            expect_list=True
        )

        self.validateOptions(evaluators, SUPPORTED_EVAL_SYSTEMS)
        self.evaluators = evaluators

        # Load Tokenizer
        tokenizer = self.fetchSettingByKey('tokenizer')
        self.validateOption(tokenizer, SUPPORTED_TOKENIZERS)
        self.tokenizer = tokenizer if tokenizer else DEFAULT_TOKENIZER

        # Load Evaluation Systems
        evaluationSystems = self.fetchSettingByKey(
            'evaluation_systems',
            expect_list=True
        )
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
        self.summarizerSwitch = Switcher(self)

        # load evaluators
        self.evaluation_library = fetchEvaluators(evaluators)
        self.evaluatorSwitch = EvaluateSwitch(self)

        sentenceCount = self.fetchSettingByKey('sentence_count')
        self.sentenceCount = int(sentenceCount) if sentenceCount \
            else DEFAULT_SENTENCE_COUNT

        self.succesfulIndicies = defaultdict(dict)  # Dict of sampleFilePaths
        # And the indices succesfully summarized, grouped by summarizer
        # This is used for evaluations. If the summarization of a specific
        # set of text fails it will not have an hypothesis. So it cannot be
        # evaluated. This is how we know which indices to skip.
        '''
            {
                'summarizer_name': {
                    'file_path_to_sanple': [0,1,3,4,6,7,8]
                                    // List of indices succesfully summarized
                }
            }
        '''
        self.sampleToSummaryMap = defaultdict(dict)

    def cacheDataFramesForSamples(self):
        textSeperator = self.textSeperator
        sampleFilePaths = self.sample_filepaths
        dataFrames = {}
        for filePath in sampleFilePaths:
            dataFrames[filePath] = pd.read_csv(
                filePath, sep=textSeperator, header=None
            )

        return dataFrames

    def cacheDataFramesForGoldSamples(self):
        textSeperator = self.textSeperator
        sampleFilePaths = self.sample_filepaths
        dataFrames = {}
        for filePath in sampleFilePaths:
            goldPath = self.generateSampleGoldFilePath(filePath)
            dataFrames[goldPath] = pd.read_csv(
                goldPath, sep=textSeperator, header=None
            )

        return dataFrames

    def walkDataSampleFolders(self):
        dataFolders = self.data_folders

        samples_filepaths = []  # Flat List of All avaialble samples

        dataSetToSampleFilesMap = {}   # Keeps track of which samples
        # belong to which datasets
        for folder in dataFolders:
            filesInFolder = glob.glob(str(os.path.join(folder, "samples/*")))
            samples_filepaths.extend(filesInFolder)
            dataSetToSampleFilesMap[folder] = filesInFolder

        return samples_filepaths, dataSetToSampleFilesMap

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
                ": Is not a supported option. Choose from: ",
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
                ": This setting is invalid. Expected True or False"
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
            targetedSettingList = targetedSetting.replace(" ", "").split(",")
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

        decodedSeperator = bytes(seperator, "utf-8").decode("unicode_escape")

        return decodedSeperator

    def runSummarizations(self, summarizerKey):
        sampleFilepaths = self.sample_filepaths
        for filepath in sampleFilepaths:
            self.runSummarizationsForSample(filepath, summarizerKey)

    def generateSummaryFilePath(self, sampleFilepath, summarizerKey):

        sampleFileName = os.path.basename(sampleFilepath)

        summaryFileName = os.path.join(
            '../data/generated_summaries/',
            '{0}_{1}'.format(
                summarizerKey, sampleFileName)
        )

        return summaryFileName

    def runSummarizationsForSample(self, sampleFilepath, summarizerKey):
        generatedSummariesFilePath = self.generateSummaryFilePath(
            sampleFilepath, summarizerKey
        )

        summarizerSwitch = self.summarizerSwitch

        dataFrames = self.dataFrames
        texts_df = dataFrames[sampleFilepath]

        succesfulIndicies = []
        summaries = []
        for row in texts_df.itertuples(index=True):
            index = row[0]
            text = row[1]
            generatedSummary = summarizerSwitch.toggleAndExecuteSummarizer(
                summarizerKey, text
            )

            if generatedSummary:
                summaries.append(generatedSummary)
                succesfulIndicies.append(index)
            else:
                summaries.append('0')

        self.succesfulIndicies[summarizerKey][sampleFilepath] = \
            succesfulIndicies

        with open(generatedSummariesFilePath, 'w') as results:
            summariesString = '\n'.join(summaries)
            results.write(summariesString)

        self.sampleToSummaryMap[summarizerKey][sampleFilepath] = \
            generatedSummariesFilePath

        '''
        self.constructGoldSubsetWithSuccesfulIndices(
            sampleFilepath, succesfulIndicies, summarizerKey
        )
        '''

    def evaluate(self, summaries, goldPath, goldIndices):
        goldSummaries = open(goldPath, 'r')
        goldSummaries = goldSummaries.readlines()
        j = 0
        print(goldIndices)
        for index in goldIndices:
            goldAbstract = goldSummaries[index]
            generatedSummary = summaries[j]
            print(rouge.get_scores(goldAbstract, generatedSummary))
            j += 1

    def constructGoldSubsetWithSuccesfulIndices(
        self, sampleFilepath, indices, summarizerKey): \

        '''
            When summaries fail you need to make sure you run the evaluators
            with the subset of the golden abstracts for the summarries that
            were successful.
        '''
        goldSubsetPath = self.generateGoldSubsetFilePath(
            sampleFilepath, summarizerKey
        )

        return goldSubsetPath

    def generateGoldSubsetFilePath(self, sampleFilepath, summarizerKey):
        sampleFileName = os.path.basename(sampleFilepath)
        fileName, ext = os.path.splitext(sampleFileName)

        sampleGoldFilePath = os.path.join(
            '../data/gold_subsets/',
            '{0}_{1}_gold{2}'.format(
                summarizerKey, fileName, ext)
        )

        return sampleGoldFilePath

    def generateSampleGoldFilePath(self, sampleFilepath):
        sampleFileFolder, sampleFileName = os.path.split(sampleFilepath)
        dataSetFileFolder, subDir = os.path.split(sampleFileFolder)
        fileName, ext = os.path.splitext(sampleFileName)

        sampleGoldFilePath = os.path.join(
            dataSetFileFolder,
            'gold',
            '{0}_gold{1}'.format(
                fileName, ext)
        )

        return sampleGoldFilePath

    def runBenchmarking(self):
        summarizerLibrary = self.summarizer_library

        for key in summarizerLibrary:
            self.runSummarizations(key)

        if self.evaluationEnabled:
            self.runEvaluations()

    def runEvaluations(self):
        for dataSet in self.dataSetToSampleFilesMap:
            self.evaluateDataSet(dataSet)

    def evaluateDataSet(self, dataset):
        sampleFilepaths = self.dataSetToSampleFilesMap[dataset]
        sampleReports = ['Report for Dataset:\t{0}\n'.format(dataset)]
        for sample in sampleFilepaths:
            sampleReports.append('\n\tReporting for Sample: {0}\n'.format(sample))
            report = self.evaluateSamplePerSummarizer(sample)
            sampleReports.extend(['\n\t\t', report])
        print(''.join(sampleReports))

    def evaluateSamplePerSummarizer(self, sampleFilepath):
        goldPath = self.generateSampleGoldFilePath(sampleFilepath)
        gold_df = self.goldDataFrames[goldPath]

        summarizerReports = []
        for summarizerKey in self.summarizers:
            summaryPath = self.sampleToSummaryMap[summarizerKey.lower()][sampleFilepath]
            summaries_df = pd.read_csv(
                summaryPath, sep='\n', header=None
            )

            summarizerReports.append(
                '\n\t\tSummarizer: {0}\n\t\t\t'.format(summarizerKey)
            )

            sampleReport = self.evaluatorSwitch\
                .executeAndReportEvaluatorsOnSample(
                    summaries_df, gold_df
                )
            summarizerReports.append(sampleReport)

        return ''.join(summarizerReports)
        '''
                goldPath = self.generateSampleGoldFilePath(sampleFilepath)
                self.evaluatorSwitch.toggleAndExecuteEvaluator()
                self.evaluate(summaries, goldPath, succesfulIndicies)
        '''


class EvaluateSwitch(object):
    def __init__(self, benchmarkInstance):
        self.sampleDataFrames = benchmarkInstance.dataFrames  # Dataframes
        # for samples are cached in the benchmark instance
        self.goldDataFrames = benchmarkInstance.goldDataFrames
        self.benchmark = benchmarkInstance
        self.evaluation_library = benchmarkInstance.evaluation_library
        self.functionMap = {
            'rouge': self.rougeScore
        }

    def executeAndReportEvaluatorsOnSample(self, summariesDF, goldTargetsDF):

        # numRows = sample_df.shape[0]
        evaluatorReportsForSample = []
        for evaluator in self.evaluation_library:
            report = self.toggleAndExecuteEvaluator(
                evaluator, summariesDF, goldTargetsDF)
            evaluatorReportsForSample.extend(report)
        return ''.join(evaluatorReportsForSample)

    def toggleAndExecuteEvaluator(self, evaluatorKey,
                                  summariesDF, goldTargetsDF):
        functions = self.functionMap

        if evaluatorKey in functions:
            method = functions[evaluatorKey]
            report = method(summariesDF, goldTargetsDF)
            return report

        error = '{0}: Is not an available evaluator'.format(evaluatorKey)
        raise ValueError(error)

    def rougeScore(self, summariesDF, goldTargetsDF):
        rouge = self.evaluation_library['rouge']

        sumRouge1 = {'f': 0.0, 'p': 0.0, 'r': 0.0}
        sumRouge2 = {'f': 0.0, 'p': 0.0, 'r': 0.0}
        sumRougel = {'f': 0.0, 'p': 0.0, 'r': 0.0}

        numSamples = 0
        for sample, goldSample in zip(summariesDF.itertuples(index=True),
                                      goldTargetsDF.itertuples(index=True)):
            goldText = goldSample[1]
            sampleHypothesisText = sample[1]
            if sampleHypothesisText == '0':  # Failed summaries default to 'O'
                continue

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
            'This is the result of the Rogue Score:\n\t\t\t',
            str(avg),
            '\n'
        ]

        return report


class Switcher(object):
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

benchmarkInstance = benchmark()
benchmarkInstance.runBenchmarking()
