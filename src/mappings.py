SUPPORTED_TOKENIZERS = ['NLTK','spaCy']
SUPPORTED_TOKENIZERS = set([tokenizer.lower() for tokenizer in SUPPORTED_TOKENIZERS])

SUPPORTED_SUMMARIZERS = ['smmrRE', 'smmry']
SUPPORTED_SUMMARIZERS = set([summarizer.lower() for summarizer in SUPPORTED_SUMMARIZERS])

SUPPORTED_EVAL_SYSTEMS = ['ROUGE', 'METEOR', 'BLEU', 'NIST', 'CIDEr']
SUPPORTED_EVAL_SYSTEMS = set([system.lower() for system in SUPPORTED_EVAL_SYSTEMS])