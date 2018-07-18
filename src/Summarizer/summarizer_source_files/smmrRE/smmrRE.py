from nltk.stem.porter import PorterStemmer
from nltk import tokenize

# from autocorrect import spell
from collections import defaultdict
from math import log


import re

from .ll import *  # import ListNode, LinkedList
from nltk.corpus import stopwords
import string

stemmer = PorterStemmer()

STOP_WORDS_SET = set(stopwords.words('english'))
LOWERCASE = set(string.ascii_lowercase).union(
    set(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
)

UPPERCASE = set(string.ascii_uppercase)


class smmrRE:
    def __init__(self, rawText):
        rawText = re.sub(' +', ' ', rawText)  # Removes double spaces
        self.stemSet = defaultdict(set)
        self.sentences = tokenize.sent_tokenize(rawText)
        self.prunedSentences = self.pruneSentences()
        self.occurences = defaultdict(lambda: 0)
        self.maxHeap = LinkedList()
        self.totalWords = 0

    def summarize(self, numSentences=5):
        numSentences = min(numSentences, len(self.sentences))
        self.associateGrammarCounterParts()
        self.assignPointsToStems()
        self.rankSentences()

        topSentencesIndicies = self.maxHeap.topIndices(numSentences)

        topSentencesIndicies.sort()

        summary = self.buildSummary(topSentencesIndicies)
        return summary

    def buildSummary(self, chronologicalTopSentenceIndices):
        sentences = self.sentences
        listOfSummarySentences = [
            sentences[ind] for ind in chronologicalTopSentenceIndices
        ]
        summary = ' '.join(listOfSummarySentences)

        return summary

    def pruneSentences(self):
        sentences = self.sentences
        prunedSentences = [
            [self.pruneWord(word) for word in sentence.split(" ")]
            for sentence in sentences
        ]

        strippedPrunedSentences = [  # Strip sentences of empty strings
            list(filter(None, sentence_word_list))
            for sentence_word_list in prunedSentences]

        return strippedPrunedSentences

    def pruneWord(self, word):
        prunedWord = ''.join(char for char in word if self.isAlpha(char))
        return prunedWord

    def isAlpha(self, char):
        return (char in LOWERCASE) or (char in UPPERCASE)

    def associateGrammarCounterParts(self):
        for sentence in self.prunedSentences:
            self.associateGrammarCounterPartsForSentence(sentence)

        return self.stemSet

    def associateGrammarCounterPartsForSentence(self, sentence):
        for word in sentence:
            wordLower = word.lower()
            if wordLower not in STOP_WORDS_SET:
                stem = stemmer.stem(wordLower)
                self.stemSet[stem].add(wordLower)
                self.occurences[stem] += 1
                self.totalWords += 1

    def assignPointsToStems(self):
        self.points = {
            stem: log(self.fetchCount(stem))
            for stem in self.stemSet
        }
        # { stem: log(self.fetchCount(stem)) for stem in self.stemSet }
        return self.points

    def fetchCount(self, stem):
        return self.occurences[stem]

    def rankSentences(self):
        sentences = self.prunedSentences

        for index in range(len(sentences)):
            sentence = sentences[index]
            popularity = self.calculateSentencePopularity(sentence)
            self.maxHeap.insertVal(popularity, index)

    def calculateSentencePopularity(self, sentence):
        wordPoints = []
        for word in sentence:
            wordLower = word.lower()
            if wordLower not in STOP_WORDS_SET:
                stem = stemmer.stem(wordLower)
                points = self.points[stem]
                wordPoints.append(points)

        if not wordPoints:
            return 0

        popularity = float(sum(wordPoints))
        # / float(len(wordPoints))

        return popularity
