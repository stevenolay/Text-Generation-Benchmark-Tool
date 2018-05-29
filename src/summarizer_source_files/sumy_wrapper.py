# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

# from sumy.parsers.html import HtmlParser
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


class sumyWrapper:
    def __init__(self, text):
        self.text = text

    def summarize(self, SENTENCES_COUNT, LANGUAGE):
        text = self.text
        # or for plain text files
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)

        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summaryList = summarizer(parser.document, SENTENCES_COUNT)
        summary = ''.join([str(sentence) for sentence in summaryList])

        return summary
