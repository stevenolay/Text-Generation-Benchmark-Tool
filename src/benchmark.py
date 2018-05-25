import configparser
import json
import glob

import pandas as pd

from summarizer_library import fetchSummarizers

from mappings import (
    SUPPORTED_EVAL_SYSTEMS,
    SUPPORTED_TOKENIZERS,
    SUPPORTED_SUMMARIZERS
)


class benchmark:
    def __init__(self):
        # Load configuration File
        self.settings = self.initSettings()

        # Load Seperators
        self.textSeperator = self.fetchSeperator('text_seperator')
        self.sentenceSeperator = self.fetchSeperator('sentence_seperator')

        # Load Summarizers
        summarizers = self.fetchSettingByKey(
            'summarizers',
            expect_list=True
        )

        self.validateOptions(summarizers, SUPPORTED_SUMMARIZERS)
        self.summarizers = summarizers

        # Load Tokenizer
        tokenizer = self.fetchSettingByKey('tokenizer')
        self.validateOption(tokenizer, SUPPORTED_TOKENIZERS)
        self.tokenizer = tokenizer

        # Load Evaluation Systems
        evaluationSystems = self.fetchSettingByKey(
            'evaluation_systems',
            expect_list=True
        )
        self.validateOptions(evaluationSystems, SUPPORTED_EVAL_SYSTEMS)
        self.evaluationSystems = evaluationSystems

        # Load States
        preTokenized = self.fetchSettingByKey('pre_tokenized')
        self.preTokenized = self.evaluateBoolean(preTokenized)

        self.data_folders = self.fetchSettingByKey(
            'data_folders',
            expect_list=True
        )

        # load filepaths of samples
        self.sample_filepaths = self.walkDataSampleFolders()

        # load summarizers
        self.summarizer_library = fetchSummarizers(summarizers)

        self.summarizerSwitch = Switcher(self)

        self.sentenceCount = int(self.fetchSettingByKey('sentence_count'))

        self.dataFrames = self.cacheDataFramesForSamples()

    def cacheDataFramesForSamples(self):
        sampleFilePaths = self.sample_filepaths
        dataFrames = {}
        for filePath in sampleFilePaths:
            dataFrames[filePath] = pd.read_csv(filePath, sep='\n', header=None)

        return dataFrames

    def walkDataSampleFolders(self):
        dataFolders = self.data_folders

        samples_filepaths = []
        for folder in dataFolders:
            filesInFolder = glob.glob(folder + "/samples/*")
            samples_filepaths.extend(filesInFolder)

        return samples_filepaths

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
        '''
        Approach adapted from Stack Overflow User:
           Jerub
        Source:
           https://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python
        '''
        settings = self.settings
        seperator = settings.get('general', key)
        decodedSeperator = bytes(seperator, "utf-8").decode("unicode_escape")

        return decodedSeperator

    def runBenchmarking(self):
        summarizerLibrary = self.summarizer_library

        for key in summarizerLibrary:
            self.runSummarizations(key)

    def runSummarizations(self, summarizerKey):
        sampleFilepaths = self.sample_filepaths
        for filepath in sampleFilepaths:
            self.runSummarizationsForSample(filepath, summarizerKey)

    def generateSummaryFilePath(self, sampleFilepath, summarizerKey):
        sampleFileNameList = sampleFilepath.split("/")
        sampleFileName = sampleFileNameList[len(sampleFileNameList) - 1]

        summaryFileName = '../data/generated_summaries/{0}_{1}'.format(
            summarizerKey, sampleFileName
        )
        return summaryFileName

    def runSummarizationsForSample(self, sampleFilepath, summarizerKey):

        generatedSummariesFilePath = self.generateSummaryFilePath(
            sampleFilepath, summarizerKey
        )
        summarizerSwitch = self.summarizerSwitch

        dataFrames = self.dataFrames
        texts_df = dataFrames[sampleFilepath]
        with open(generatedSummariesFilePath, 'w') as summaries:
            for row in texts_df.itertuples(index=True):
                index = row[0]
                text = row[1]
                generatedSummary = summarizerSwitch.toggleAndExecuteSummarizer(
                    summarizerKey, text
                )

                if(index < len(texts_df) - 1):
                    summaries.write('{0}\n'.format(generatedSummary))
                else:
                    summaries.write('{0}'.format(generatedSummary))


class Switcher(object):
    def __init__(self, benchmarkInstance):
        self.benchmark = benchmarkInstance
        self.summarizer_library = benchmarkInstance.summarizer_library
        self.functionMap = {
            'smmrre': self.smmrre
        }

    def toggleAndExecuteSummarizer(self, summarizerKey, text):
        functions = self.functionMap

        if summarizerKey in functions:
            method = functions[summarizerKey]
            return method(text)  # Method should return a summary
        error = '{0}: Is not an available summarizer'.format(summarizerKey)
        raise ValueError(error)

    def joinTokenizedSentences(self, text):
        benchmark = self.benchmark
        sentenceSeperator = benchmark.sentenceSeperator
        newText = text.replace(sentenceSeperator, '')
        return newText

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


benchmarkInstance = benchmark()
benchmarkInstance.runBenchmarking()
