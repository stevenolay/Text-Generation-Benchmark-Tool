import sys
sys.path.insert(0, 'summarizer_source_files')

from smmrRE import smmrRE
from sumy_wrapper import sumyWrapper

sumyKeys = [
    'sumylsa', 'sumyluhn', 'sumykl', 'sumylexrank',
    'sumyrandom', 'sumyedmundsonkey', 'sumyedmundsonlocation',
    'sumyedmundsoncue', 'sumyedmundson', 'sumyedmundsontitle',
    'sumysumbasic', 'sumytextrank'
]


def fetchSummarizers(enabledSummarizers):
    sumyWrap = sumyWrapper()
    SUMMARIZERS = {
        'smmrre': smmrRE,
    }

    sumySummarizers = {k: sumyWrap.summarize(k) for k in sumyKeys}

    SUMMARIZERS.update(sumySummarizers)

    enabledSummarizers = [
        summarizer.lower() for summarizer in enabledSummarizers
    ]

    desiredSummarizers = dict(
        (k.lower(), SUMMARIZERS[k])
        for k in enabledSummarizers
        if k in SUMMARIZERS
    )

    return desiredSummarizers
