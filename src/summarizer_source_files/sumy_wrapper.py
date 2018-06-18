# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

# from sumy.parsers.html import HtmlParser

from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.kl import KLSummarizer
from sumy.summarizers.random import RandomSummarizer
from sumy.summarizers.edmundson_key import EdmundsonKeyMethod
from sumy.summarizers.edmundson_location import EdmundsonLocationMethod
from sumy.summarizers.edmundson_cue import EdmundsonCueMethod
from sumy.summarizers.edmundson import EdmundsonSummarizer
from sumy.summarizers.edmundson_title import EdmundsonTitleMethod
from sumy.summarizers.sum_basic import SumBasicSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


class sumyWrapper:
    def __init__(self):
        self.sumySummarizerMap = {
            'sumylsa': LsaSummarizer,
            'sumyluhn': LuhnSummarizer,
            'sumykl': KLSummarizer,
            'sumylexrank': LexRankSummarizer,
            'sumyrandom': RandomSummarizer,
            'sumyedmundson': EdmundsonSummarizer,
            'sumysumbasic': SumBasicSummarizer,
            'sumytextrank': TextRankSummarizer
        }

        self.specialMethods = {
            'sumyedmundsonkey': self.summarizeEdmundsonKey,
            'sumyedmundsonlocation': self.summarizeEdmundsonLocation,
            'sumyedmundsoncue': self.summarizeEdmundsonCue,
            'sumyedmundsontitle': self.summarizeEdmundsonTitle
        }
        '''
            Special methods require additional positional arguments.
            These arguments are weight related. Feel free to adjust
            these weights to your needs. They will result in varied
            evaluation scores.
        '''

    def summarize(self, target):
        if target in self.specialMethods:
            return self.specialMethods[target]

        summarizerMap = self.sumySummarizerMap
        summarizerClass = summarizerMap[target]

        def summarizeFunc(text, SENTENCES_COUNT, LANGUAGE):
            parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))

            stemmer = Stemmer(LANGUAGE)

            summarizer = summarizerClass(stemmer)
            summarizer.stop_words = get_stop_words(LANGUAGE)

            summarizer.bonus_words = parser.significant_words
            summarizer.stigma_words = parser.stigma_words

            summaryList = summarizer(parser.document, SENTENCES_COUNT)
            summary = ''.join([str(sentence) for sentence in summaryList])

            return summary
        return summarizeFunc

    def summarizeEdmundsonKey(self, text, SENTENCES_COUNT, LANGUAGE):
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))

        stemmer = Stemmer(LANGUAGE)

        bonusWords = parser.significant_words
        summarizer = EdmundsonKeyMethod(stemmer, bonusWords)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        weight = 1.0
        summaryList = summarizer(parser.document, SENTENCES_COUNT, weight)
        summary = ''.join([str(sentence) for sentence in summaryList])

        return summary

    def summarizeEdmundsonLocation(self, text, SENTENCES_COUNT, LANGUAGE):
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))

        stemmer = Stemmer(LANGUAGE)

        nullWords = get_stop_words(LANGUAGE)
        summarizer = EdmundsonLocationMethod(stemmer, nullWords)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        w_h = 1
        w_p1 = 1
        w_p2 = 1
        w_s1 = 1
        w_s2 = 1
        summaryList = summarizer(
            parser.document, SENTENCES_COUNT, w_h, w_p1, w_p2, w_s1, w_s2)
        summary = ''.join([str(sentence) for sentence in summaryList])

        return summary

    def summarizeEdmundsonCue(self, text, SENTENCES_COUNT, LANGUAGE):
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))

        stemmer = Stemmer(LANGUAGE)
        bonusWords = parser.significant_words
        stigmaWords = parser.stigma_words
        summarizer = EdmundsonCueMethod(stemmer, bonusWords, stigmaWords)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        bunus_word_weight = 1
        stigma_word_weight = 1
        summaryList = summarizer(
            parser.document, SENTENCES_COUNT,
            bunus_word_weight, stigma_word_weight)

        summary = ''.join([str(sentence) for sentence in summaryList])

        return summary

    def summarizeEdmundsonTitle(self, text, SENTENCES_COUNT, LANGUAGE):
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))

        stemmer = Stemmer(LANGUAGE)

        nullWords = get_stop_words(LANGUAGE)
        summarizer = EdmundsonTitleMethod(stemmer, nullWords)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summaryList = summarizer(parser.document, SENTENCES_COUNT)
        summary = ''.join([str(sentence) for sentence in summaryList])

        return summary
