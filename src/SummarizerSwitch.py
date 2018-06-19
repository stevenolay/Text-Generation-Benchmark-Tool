from summarizer_library import sumyKeys as SUMY_KEYS


class SummarizerSwitch(object):
    def __init__(self, benchmarkInstance):
        self.benchmark = benchmarkInstance
        self.summarizer_library = benchmarkInstance.summarizer_library

        sumyKeys = SUMY_KEYS
        sumyFunctionMap = {k: self.sumySwap(k) for k in sumyKeys}

        self.functionMap = {
            'smmrre': self.smmrre,
        }

        self.functionMap.update(sumyFunctionMap)

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

    def sumySwap(self, sumyMethodKey):
        def sumyFunc(text):
            benchmark = self.benchmark
            numSentences = benchmark.sentenceCount

            if benchmark.preTokenized:
                # sumy has it's own tokenizer
                text = self.joinTokenizedSentences(text)

            summarizer = self.summarizer_library[sumyMethodKey]
            summary = summarizer(text, numSentences, 'english')

            return summary
        return sumyFunc
