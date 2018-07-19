from .summarizer_source_files.smmrRE.smmrRE import smmrRE
from .summarizer_source_files.sumy_wrapper import sumyWrapper
from .summarizer_source_files.Sedona import Sedona
from .summarizer_source_files.Recollect import Recollect

sumyKeys = [
    'sumylsa', 'sumyluhn', 'sumykl', 'sumylexrank',
    'sumyrandom', 'sumyedmundsonkey', 'sumyedmundsonlocation',
    'sumyedmundsoncue', 'sumyedmundson', 'sumyedmundsontitle',
    'sumysumbasic', 'sumytextrank'
]


def fetchSummarizers(enabledSummarizers):
    '''
        input: list of summarizer keys
        output: dict(
                    summarizerKey: summarizerMethod
                                 (None if no method is specified))
        purpose: Onload of summarizer switch the output of this function
        is provided to prevent cluttering the file with library
        imports. The output dictionary can be interfaced to
        fetch the summarizer function desired.

        If no library is specified this will return a None type.
        It is then the responsibility of the user to load their library in
        presumably directly in the SummarizerSwitch.
    '''
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

    desiredSummarizers = dict(
        (k.lower(), SUMMARIZERS[k.lower()])
        if k.lower() in SUMMARIZERS else (k, None)
        for k in enabledSummarizers
    )

    return desiredSummarizers
