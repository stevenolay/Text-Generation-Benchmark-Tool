SUPPORTED_TOKENIZERS = ['NLTK', 'spaCy']
SUPPORTED_TOKENIZERS = set(
    [tokenizer.lower() for tokenizer in SUPPORTED_TOKENIZERS]
)

SUPPORTED_SUMMARIZERS = [
    'smmrRE', 'smmry', 'sumyLSA',
    'sumyLuhn', 'sumyKL', 'sumyLexRank',
    'sumyRandom', 'sumyEdmundsonKey',
    'sumyEdmundsonLocation', 'sumyEdmundsonCue',
    'sumyEdmundson', 'sumyEdmundsonTitle',
    'sumySumBasic', 'sumyTextRank', 'Sedona',
    'Recollect'
]

SUPPORTED_SUMMARIZERS = set(
    [summarizer.lower() for summarizer in SUPPORTED_SUMMARIZERS]
)

SUPPORTED_EVAL_SYSTEMS = [
    'ROUGE', 'METEOR', 'BLEU', 'NIST', 'CIDEr', 'pyRouge'
]

SUPPORTED_EVAL_SYSTEMS = set(
    [system.lower() for system in SUPPORTED_EVAL_SYSTEMS]
)
DEFAULT_TOKENIZER = 'NLTK'
DEFAULT_TEXT_SEPERATOR = '\n'
DEFAULT_SENTENCE_SEPERATOR = '[BREAK]'
DEFAULT_SENTENCE_COUNT = 3
