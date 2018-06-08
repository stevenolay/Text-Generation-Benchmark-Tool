import sys
sys.path.insert(0, 'summarizer_source_files')

from smmrRE import smmrRE
from sumy_wrapper import sumyWrapper


def fetchSummarizers(enabledSummarizers):

    SUMMARIZERS = {
        'smmrre': smmrRE,
        'sumy': sumyWrapper
    }

    enabledSummarizers = [
        summarizer.lower() for summarizer in enabledSummarizers
    ]

    desiredSummarizers = dict(
        (k.lower(), SUMMARIZERS[k])
        for k in enabledSummarizers
        if k in SUMMARIZERS
    )

    return desiredSummarizers
