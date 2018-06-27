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
```
Some summarizers require the NLTK tokenizer which has an extra build step:

```python
    >>> import nltk
    >>> nltk.download('stopwords')
```
### <a name="supported_s"></a> Supported Summarizers
This application has default support for all of the SUMY summarizers.

SUMY Edmonson Summarizers have weight attributes, null words, and stop words that have been hard set. If you would like to alter these values, which are hard set to the defaults present in the Edmunson Summarizer. Edit the weights in src/summarizer_source_files/sumy_wrapper.py . There are placeholders for all the parameters that can be changed to suit your needs.

This application supports Adobe's Sedona and Recollect summarizers.

This application also supports a stemmed TF rank summarizer called smmrRE made by Steven Layne.

### <a name="supported_m"></a> Supported Metrics

This application supports pyRouge* , rouge (a pure python implementation of ROUGE score), and METEOR.

### <a name="settings"></a> Supported Metrics

Refer to src/settings.ini for the avaialble settings. You can chain metrics and summarizers together by listing your desired summarizers and metrics in a comma seperated format (CASE INSENSITVE).

### <a name="running"></a> Running Benchmark
```
$ python src/benchmark.py
```

## <a name="directory-structure"></a> Directory structure
```
.
├── README.md
├── data
│   ├── example_dataset_en
│   │   ├── gold
│   │   │   └── corpus-000000_gold.txt
│   │   └── samples
│   │       └── corpus-000000.txt
│   └── generated_summaries
└── src
    ├── SummarizerSwitch.py
    ├── benchmark.py
    ├── evaluator_library.py
    ├── evaluator_source_files
    │   ├── Meteor
    │   │   ├── Meteor.py
    │   │   ├── __init__.py
    │   │   ├── data
    │   │   │   └── paraphrase-en.gz
    │   │   └── meteor-1.5.jar
    │   └── __init__.py
    ├── mappings.py
    ├── settings.ini
    ├── summarizer_library.py
    ├── summarizer_source_files
    │   ├── Recollect.py
    │   ├── Sedona.py
    │   ├── __init__.py
    │   ├── ll.py
    │   ├── smmrRE.py
    │   └── sumy_wrapper.py
    └── utils.py
```
