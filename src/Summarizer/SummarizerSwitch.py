from .SummarizerLibrary import sumyKeys as SUMY_KEYS
from tools.logger import Logger
LOGGER = Logger.getInstance()


class SummarizerSwitch(object):
    def __init__(self, benchmarkInstance):
        self.benchmark = benchmarkInstance
        #  Refer to tools/tokenizer.py
        self.tokenizer = benchmarkInstance.tokenizer

        self.summarizerLibrary = benchmarkInstance.summarizerLibrary

        sumyKeys = SUMY_KEYS
        sumyFunctionMap = {
            k: self._sumySwap(k)
            for k in sumyKeys
        }

        self.functionMap = {
            'smmrre': self._smmrre,
            'sedona': self._sedona,
            'recollect': self._recollect
        }

        self.functionMap.update(sumyFunctionMap)

        self.functionMap = dict(
            (k.lower(), v)
            for k, v in self.functionMap.items()
        )

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
            summary = None
            try:
                method = functions[summarizerKey]
                # Method should return a summary
                summary = method(text)
            except Exception as err:
                # Failed summaries are logged so they can be investigated.
                LOGGER.error(str(err))

            return summary

        error = '{0}: Is not an available summarizer'.format(summarizerKey)
        raise ValueError(error)

    def _recollect(self, text):
        benchmark = self.benchmark
        numSentences = benchmark.sentenceCount

        if benchmark.preTokenized:
            # recollect expects text to not be pretokenized
            text = self.joinTokenizedSentences(text)

        RecollectClass = self.summarizerLibrary['recollect']
        LANGUAGE = 'en'
        recollect = RecollectClass(LANGUAGE)

        summary = recollect.summarize(text, numSentences)

        return summary

    def _sedona(self, text):
        benchmark = self.benchmark
        numSentences = benchmark.sentenceCount

        if benchmark.preTokenized:
            # sedona expects text to not be pretokenized
            text = self.joinTokenizedSentences(text)

        SedonaClass = self.summarizerLibrary['sedona']
        sedona = SedonaClass()

        summary = sedona.summarize(text, numSentences)

        return summary

    def _smmrre(self, text):
        benchmark = self.benchmark
        numSentences = benchmark.sentenceCount

        if benchmark.preTokenized:
            # smmrRE expects text to not be pretokenized
            text = self.joinTokenizedSentences(text)

        smmrREClass = self.summarizerLibrary['smmrre']
        smmrRE = smmrREClass(text)

        summary = smmrRE.summarize(numSentences)

        return summary

    def _sumySwap(self, sumyMethodKey):
        def sumyFunc(text):
            benchmark = self.benchmark
            numSentences = benchmark.sentenceCount

            if benchmark.preTokenized:
                # sumy has it's own tokenizer
                text = self.joinTokenizedSentences(text)

            summarizer = self.summarizerLibrary[sumyMethodKey]
            summary = summarizer(text, numSentences, 'english')

            return summary
        return sumyFunc
