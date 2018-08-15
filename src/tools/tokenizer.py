from __future__ import unicode_literals, print_function
from nltk import word_tokenize, sent_tokenize
import spacy
from tools.defaults import (
    SUPPORTED_TOKENIZERS
)


class Tokenizer:
    def __init__(self, targetTokenizer):
        self.validateTargetTokenizer(targetTokenizer)
        self.targetTokenizer = targetTokenizer

        self.sentenceTokenizerMap = {
            'nltk': self._nltk_sent_tokenize,
            'spacy': self._spacy_sent_tokenize
        }

        self.wordTokenizerMap = {
            'nltk': self._nltk_word_tokenize,
            'spacy': self._spacy_word_tokenize
        }

        self.nlp = spacy.load('en')

    def validateTargetTokenizer(self, targetTokenizer):
        if targetTokenizer.lower() not in SUPPORTED_TOKENIZERS:
            error = [
                targetTokenizer,
                ': Is not supported. Expected {0}'.format(
                    ', '.join(list(SUPPORTED_TOKENIZERS)))
            ]
            raise ValueError(''.join(error))

    def sent_tokenize(self, sourceString):
        return self.sentenceTokenizerMap[
            self.targetTokenizer.lower()](sourceString)

    def word_tokenize(self, sourceString):
        return self.wordTokenizerMap[
            self.targetTokenizer.lower()](sourceString)

    def _nltk_sent_tokenize(self, sourceString):
        sentences = sent_tokenize(sourceString)
        return sentences

    def _nltk_word_tokenize(self, sourceString):
        words = word_tokenize(sourceString)
        return words

    def _spacy_sent_tokenize(self, sourceString):
        doc = self.nlp(sourceString)

        sentences = [
            ''.join(token.string for token in sentence)
            for sentence in doc.sents
        ]

        return sentences

    def _spacy_word_tokenize(self, sourceString):
        doc = self.nlp(sourceString)
        sentences = doc.sents

        tokens = []

        for sentence in sentences:
            sentTokens = [token.string for token in sentence]
            tokens.extend(sentTokens)

        return tokens
