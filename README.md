# Summarization Benchmark Tool

## Table of contents:
- [Requierments](#Requirements)
- [Getting started](#getting-started)
  - [Cloning the repo](#cloning)
  - [Installing dependencies](#installing)
  - [Supported Summarizers](#supported_s)
  - [Supported Metrics](#supported_m)
  - [Settings](#settings)
  - [Running](#running)
- [Directory structure](#directory-structure)
- [Adding Datasets](#dataset)
    - [Formatting Datasets](#dataset_f)
- [Adding to Source Code](#source_code)
    - [Big Picture](#source_bp)
    - [Adding Summarizers](#summarizer_a)
    - [Adding Metrics](#metrics_a)

## <a name="Requirements"></a> Requirements
The Summarization Benchmark Tool requires Python 3 or 2 and pip.

The configuration file [`src/settings.ini`](src/settings.ini) contains parameters than can be altered. Options and explanations of these parameters are found inline.

## <a name="getting-started"></a> Getting started
### <a name="cloning"></a> Cloning the repo
```
$ git clone https://github.com/stevenolay/Summarization-Benchmark-Tool.git
$ cd Summarization-Benchmark-Tool
```

### <a name="installing"></a> Installing dependencies
```
$ pip install -r requirements.txt
$ python -m spacy download en
```
Some summarizers require the NLTK tokenizer which has an extra build step:

```python
    >>> import nltk
    >>> nltk.download('stopwords')
    >>> nltk.download('punkt')
```

### <a name="supported_s"></a> Supported Summarizers
This application has default support for all of the SUMY summarizers.

SUMY Edmonson Summarizers have weight attributes, null words, and stop words that have been hard set. If you would like to alter these values, which are hard set to the defaults present in the Edmunson Summarizer, edit the values in src/summarizer_source_files/sumy_wrapper.py . There are placeholders for all the parameters that can be changed to suit your needs.

This application supports Adobe's Sedona and Recollect summarizers. Sedona and Recollect have paramaters that can be changed in the functions createRequestBody and createSedonaRequestBody in src/summarizer_source_files/Recollect.py and src/summarizer_source_files/Recollect.py respectively.

This application also supports a stemmed TF rank summarizer called smmrRE made by Steven Layne. It is a re-implementation of SMMRY as outlined here [SMMRY Algorithm Description](https://smmry.com/about)

### <a name="supported_m"></a> Supported Metrics

This application supports pyRouge[1] , rouge (a pure python implementation of ROUGE score), and METEOR[2].

[1] In order to use pyRouge you must have it preinstalled on your machine. pyRouge is a very tricky to setup.  [Refer to the pyRouge docs](https://github.com/bheinzerling/pyrouge) for installation instructions.
[2] Meteor is included in this application. However, you must have the JAVA SDK installed on your machine and it is only configured for English. The Meteor installation directory is src/evaluator_source_files/Meteor. The language files are found at src/evaluator_source_files/Meteor/data.

If you would like to add additional languages download Meteor 1.5 [here](http://www.cs.cmu.edu/~alavie/METEOR/download/meteor-1.5.tar.gz). Extract the contents and copy the language files located in the data/ folder to src/evaluator_source_files/Meteor/data.

### <a name="settings"></a> Settings

Refer to src/settings.ini for the available settings. You can run multiple metrics and summarizers by listing your desired summarizers and metrics in a comma seperated format (CASE INSENSITVE).

### <a name="running"></a> Running Benchmark Tool
```
$ cd src
$ python benchmark.py
```

## <a name="directory-structure"></a> Directory structure
```
.
├── README.md
├── data
│   ├── example_dataset_en
│   │   ├── gold
│   │   │   ├── corpus-000000_gold.txt
│   │   └── samples
│   │       └── corpus-000000.txt
├── parsers
│   ├── arxivParser
│   │   └── parser.py
│   └── DUCParser.py
├── requirements.txt
└── src
    ├── Evaluator
    │   ├── EvaluatorLibrary.py
    │   ├── EvaluatorSwitch.py
    │   └── evaluator_source_files
    │       |── Meteor
    │           ├── Meteor.py
    │           ├── data
    │           │   └── paraphrase-en.gz
    │           └── meteor-1.5.jar
    ├── Summarizer
    │   ├── SummarizerLibrary.py
    │   ├── SummarizerSwitch.py
    │   └── summarizer_source_files
    │       ├── Recollect.py
    │       ├── Sedona.py
    │       ├── smmrRE
    │       │   ├── ll.py
    │       │   └── smmrRE.py
    │       └── sumy_wrapper.py
    ├── benchmark.py
    ├── settings.ini
    └── tools
        ├── SRO.py
        ├── defaults.py
        ├── plot.py
        └── utils.py
```
## <a name="dataset"></a> Adding Datasets
Datasets are intended to be stored in data/ but you are able to provide comma seperated absolute and relative paths to datasets stored elsewhere in the src/settings.ini file under general -> data_sets. Note: Even datasets stored in data/ must be specified in the settings.ini. This version does not support autodetection of datasets.

### <a name="dataset_f"></a> Formatting Datasets
Datasets should contain 2 subfolders: 'gold/' and 'samples/'. Gold should contain your model examples and Samples should hold your target documents for summarization. Your corpora examples should be line seperated. Gold files should have the same name as the samples with a `_gold` Files that do not follow this format cannot be discovered by this application. Although documents must be line seperated summarizers do not. You are free to use sentence tags. Specify the sentence tag seperator in src/settings.ini in general -> sentence_seperator. You must also set general -> preTokenized to true.

### <a name="source_code"></a> Adding to Source Code
This benchmark tool is designed with the intention of making it straightforward to add and remove summarizers and metrics.

### <a name="source_bp"></a> Big Picture
There are a few key folders and files that you must interface with in order to add summarizers and metrics.

#### Key Folders:
1.  src/summarizer_source_files
    - Location where you should store your abstract interfaces(wrappers) for summarizers.
    - Some summarizers may need to interact with other programming languages. A wrapper interface can be used to handshake between python and those summarizers.
2.  src/evaluator_source_files
    - Location where you should store your abstract interfaces(wrappers) for metrics.
    - Some may need to interact with other programming languages. A wrapper interface can be used to handshake between python and those summarizers.

#### Key Files:
1. src/benchmark.py
    - Self-executing class that runs summarization and evaluations based on the settings specified in src/settings.ini
2. src/tools/defaults.py
    - Contains all the settings defaults and supported summarizers and metrics.
    - Newely atted summarizers and metrics must be added to the supported lists.
3. src/Summarizer/SummarizerLibrary.py
    - Loads in summarizer libraries and wrappers.
    - Contains function fetchSummarizers that expects a list of Strings, that reference targeted summarizers. It returns a dictionary where the keys are the summarizer and the value is the class object for the summarizer you would like to use.
4. src/Evaluator/EvaluatorLibrary.py
    - Loads in metric tool libraries and wrappers.
    - Contains function fetchEvaluators that expects a list of Strings, that reference targeted evaluators. It returns a dictionary where the keys are the evaluator and the value is the class object for the evaluator you would like to use.
5.  src/Summarizer/SummarizerSwitch.py
    - Class that contains methods to call on summarizers.
    - function toggleAndExecuteSummarizer()
        - Inputs: summarizerKey(String), takes in a the key to a summarizer. text(String), String to summarize.
        - Output: summarized text, summarized using the targeted summarizer.
        - Maps summarizer to a private methods that reformats text and calls the library for that targeted summarizer. Output of the method is returned to the caller of this function.
6.  src/Evaluator/EvaluatorSwitch.py
    - Class that contains methods to call on summarizers.
    - function executeAndReportEvaluatorsOnCorpus()
        - Inputs: SRO(SummaryReaderObject) used to fetch hypotheses and their corresponding references.
        - Output: Reports for the hypothesis and their references across the specified metrics.

### <a name="summarizer_a"></a> Adding Summarizers
1. Navigate to src/Summarizer/SummarizerSwitch.py
2. Create a private(\_) method for your summarizer.
    - \_privateMethod(self, text)
    - Input: Text to summarize(String)
    - Output: Summarized Text(String)
    - Note: SummarizerSwitch Class contains some helpful attributes:
        - self.benchmark.sentenceCount (int) -> Number of Sentences specified in configuration file('src/settings.ini')
        - self.benchmark.preTokenized (BOOLEAN) -> Tells you wether or not the text is already tokenized.
        - self.joinTokenizedSentences(text) (Function) -> Returns text with tokenization removed.
        - self.splitTokenizedSentences(text) (Function) -> Returns list(String) with text split by sentence seperator.
3. Add it to class member self.functionMap in the class's constructor(\_\_init\_\_)
    - Key: String, Indentifier for your summarizer.
    - Value: self.\_privateMethod()
4. Navigate to src/defaults.py
5. Place the identifier(Case Insensitive) for your private method in the SUPPORTED_SUMMARIZERS list.
6. To run the benchmark tool with your summarizer update the settings.ini to include your identifier(Case Insensitive), and run the tool.

### <a name="metrics_a"></a> Adding Metrics
1. Navigate to src/Evaluator/EvaluatorSwitch.py
2. Create a private(\_) method for your evaluator.
    - \_privateMethod(self, SRO)
    - input: SRO(Summary Reader Object)
        - This object contains two public methods:
            - SRO.readOne()
                - Output:  tuple( String, list(String) ) -> (hypothesis, references)
                - Returns a tuple with the first element the hypothesis and the second element the list of references.
            - SRO.readAll()
                - Output: list( tuple( String, list(String) ) ) -> [(hypothesis, references),...]
            - SRO.length or len(SRO)
                - Output: int -> number of summaries.
    - Output: Report(String) -> results of the metric calculations.
3. Add it to class member self.functionMap in the class's constructor(\_\_init\_\_)
    - Key: String, Indentifier for your Evaluator(Case Insensitive)
    - Value: self.\_privateMethod()
4. Navigate to src/tools/defaults.py
5. Place the identifier(Case Insensitive) for your private method in the SUPPORTED_EVAL_SYSTEMS list.
6. To run the benchmark tool with your metric update the settings.ini to include your identifier(Case Insensitive), and run the tool.
