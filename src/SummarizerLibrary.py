from summarizer_source_files.smmrRE.smmrRE import smmrRE
from summarizer_source_files.sumy_wrapper import sumyWrapper
from summarizer_source_files.Sedona import Sedona
from summarizer_source_files.Recollect import Recollect

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
        'sedona': Sedona,
        'recollect': Recollect
    }

    sumySummarizers = {
        k: sumyWrap.summarize(k)
        for k in sumyKeys
    }

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
