from nltk.translate.nist_score import sentence_nist
from nltk.tokenize.nist import NISTTokenizer
ntok = NISTTokenizer()


def compute_nist(hypothesis, references):
    hypothesis = list(ntok.tokenize(hypothesis))

    references = [
        list(ntok.tokenize(reference)) for reference in references
    ]

    return sentence_nist(references, hypothesis)
