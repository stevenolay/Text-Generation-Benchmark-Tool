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
```
Some summarizers require the NLTK tokenizer which has an extra build step:

```python
    >>> import nltk
    >>> nltk.download('stopwords')
```
### <a name="supported_s"></a> Supported Summarizers
This application has default support for all of the SUMY summarizers.

SUMY Edmonson Summarizers have weight attributes, null words, and stop words that have been hard set. If you would like to alter these values, which are hard set to the defaults present in the Edmunson Summarizer, edit the values in src/summarizer_source_files/sumy_wrapper.py . There are placeholders for all the parameters that can be changed to suit your needs.

This application supports Adobe's Sedona and Recollect summarizers. Sedona and Recollect have paramaters that can be changed in the functions createRequestBody and createSedonaRequestBody in src/summarizer_source_files/Recollect.py and src/summarizer_source_files/Recollect.py respectively.

This application also supports a stemmed TF rank summarizer called smmrRE made by Steven Layne. It is a re-implementation of SMMRY as outlined here [SMMRY Algorithm Description](https://smmry.com/about)

### <a name="supported_m"></a> Supported Metrics

This application supports pyRouge* , rouge (a pure python implementation of ROUGE score), and METEOR.

### <a name="settings"></a> Settings

Refer to src/settings.ini for the available settings. You can run multiple metrics and summarizers by listing your desired summarizers and metrics in a comma seperated format (CASE INSENSITVE).

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
## <a name="dataset"></a> Adding Datasets
Datasets are intended to be stored in data/ but you are able to provide comma seperated absolute and relative paths to datasets stored elsewhere in the src/settings.ini file under general -> data_sets. Note: Even datasets stored in data/ must be specified in the settings.ini. This version does not support autodetection of datasets.
### <a name="dataset_f"></a> Formatting Datasets
```
Data sets should contain 2 subfolders. 'gold/' and 'samples/'. Gold should hold your model examples and Samples should hold your target documents for summarization.

Your corpora examples should be line seperated. Gold files should have the same name as the samples with a '_gold' suffix before the file extension. Files that do not follow this format cannot be discovered by this application. Although documents must be line seperated summarizers do not. You are free to use sentence tags. Specify the sentence tag seperator in src/settings.ini in general -> sentence_seperator. You must also set general -> preTokenized to true.
```
## <a name="dataset"></a> Adding Datasets
Datasets are intended to be stored in data/ but you are able to provide comma seperated absolute and relative paths to datasets stored elsewhere in the src/settings.ini file under general -> data_sets. Note: Even datasets stored in data/ must be specified in the settings.ini. This version does not support autodetection of datasets.
