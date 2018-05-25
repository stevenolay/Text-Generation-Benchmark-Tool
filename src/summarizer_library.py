import sys
sys.path.insert(0, 'summarizer_source_files')

from smmrRE import smmrRE

def fetchSummarizers(enabledSummarizers):

  SUMMARIZERS = {
    'smmrre': smmrRE
  }

  enabledSummarizers = [summarizer.lower() for summarizer in enabledSummarizers]
  

  desiredSummarizers = dict((k, SUMMARIZERS[k]) for k in enabledSummarizers if k in SUMMARIZERS)

  return desiredSummarizers



  '''

  import sys
sys.path.insert(0, 'summarizer_source_files')

from smmrRE import smmrRE

def runSummarizations(benchmarkInstance):
  benchmarkInstance.sentenceSeperator

  if not str(type(benchmarkInstance)) == "<class '__main__.benchmark'>":
    raise Exception("This library cannot be called directly. Must be called from the benchmark tool.")

  SUMMARIZERS = {
    'smmrre': smmrRE
  }

  return SUMMARIZERS


  '''