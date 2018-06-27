# Summarization Benchmark Tool

## Table of contents:
- [Requierments](#Requirements)
- [Getting started](#getting-started)
  - [Cloning the repo](#cloning)
  - [Installing dependencies](#installing)
  - [Testing](#testing)
  - [Building](#building)
  - [Running locally](#running)
- [Directory structure](#directory-structure)

## <a name="Requirements"></a> Requirements
The Summarization Benchmark Tool requires Python 3 or 2, as well as a few Python packages that you may install running pip install -r requirements.txt.

The configuration file [`src/settings.ini`](src/settings.ini) contains parameters than can be altered. Options and explanations of these parameters are found inline.

## <a name="getting-started"></a> Getting started
### <a name="cloning"></a> Cloning the repo
```
$ git clone https://github.com/Quibbl/quibbl-web-app.git
$ cd quibbl-web-app
```

### <a name="installing"></a> Installing dependencies
```
$ pip install -r requirements.txt

Some summarizers require the NLTK tokenizer which has an extra build step:
.. code-block:: python
    >>> import nltk
    >>> nltk.download('stopwords')
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
    │   │   ├── Meteor.pyc
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
