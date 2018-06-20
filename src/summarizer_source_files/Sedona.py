import requests
import re
import math


class Sedona:
    def __init__(self):

        self.URL = 'http://multicore4t5500/analyzer2.0'
        self.highlightCoverage = 0.15
        self.charsPerSentence = 150
        self.charsPerWord = 6
        self.numSummaries = 1

    def processText(self, text):
        '''
            Input: Text
            Output: Text stripped of all ASCII Characters
        '''
        return re.sub(r'[^\x00-\x7f]', r'', text)

    def createSedonaRequestBody(self, text):
        numSentences = len(text) / self.charsPerSentence
        sentsPerSummary = math.floor(
            self.highlightCoverage * numSentences / self.numSummaries
        )
        sentsPerSummary = max(sentsPerSummary, 2)

        padSentsPerSummary = math.floor(max(sentsPerSummary * 1.5, 5))

        body = {
            "lang": "EN",
            "fmt": "json_all",
            "ngists": self.numSummaries,
            "nterms": 7,
            "cgtgtsents": sentsPerSummary,
            "nsents": padSentsPerSummary,
            "ncat": 7,
            "nlvl": 8,
            "nent": "none",
            "tags": "none",
            "extensions": "",
            "ichains": 3,
            "ilevels": 1,
            "ngramsreq": 100,
            "ngramtype": "bigrams",
            "stopwords": "remove",
            "ngramproc": "enumerate",
            "ngramcutoff": 1,
            "capseq": "None",
            "ontoname": "tm.onto.EN",
            "req": "Upload Text",
            "text": text,
            "url": "",
            "jsrules": "phantomExtractTitle.js, phantomExtractText.js",
            "lmstats": "none",
            "trace": "on",
            "treefmt": "L-R,T-B",
            "ns": "none",
            "analysis": "statNgramFinder,statSummarizer,statAutoTagger,"
            "statSolrTagger,nlpxAutoTagger,nlpxPOSTagger,nlpxEmoSentiTagger"
        }

        return body

    def summarize(self, text, numSentences):
        '''
            Consider setting sentsPerSummary to
            numSentences.
        '''
        processedText = self.processText(text)

        sedonaJSON = self.createSedonaRequestBody(processedText)

        r = requests.post(self.URL, data=sedonaJSON)
        r.raise_for_status()

        sedonaRespJSON = r.json()

        return self.combineTopNSentences(sedonaRespJSON, numSentences)

    def combineTopNSentences(self, sedonaRespJSON, N):
        text = sedonaRespJSON["theme gists"]["S0001"]["text"]
        N = min(len(text) - 1, N)
        combined = ''.join([text[i]["docText"] for i in range(N)])
        return combined
