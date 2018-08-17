from tools.utils import createFolderIfNotExists
from datetime import datetime
import plotly.figure_factory
import plotly.offline
import json

import os
import csv
import codecs
from collections import defaultdict

import pandas as pd

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages

import seaborn as sns
sns.set_context("talk")
sns.set_style("white")

createFolderIfNotExists("../figs")


class reportTreeReformatter:

    def __init__(self, metrics, reportTree):
        self.metrics = metrics
        self.reportTree = reportTree
        self.reportTreeFlattenedByCorpus = self.flatCorpForm()

    def flatCorpForm(self):
        reportTree = self.reportTree
        '''
        reportTree
        {
            'dataset':{
                'corpus':{
                    'summarizer':{
                        'metric': report
                    }
                }
            }
        }
        '''

        dataSetDicts = [reportTree[dataset] for dataset in reportTree]

        corpusFlat = {}
        [corpusFlat.update(dataSetDicts[i]) for i in range(len(dataSetDicts))]
        '''
            corpusFlat = {
            '../data/DUC_multi/samples/DUC-2004.txt': {
                'smmrRE': {'meteor': 0.1685136779914727},
                'sumyLSA': {'meteor': 0.15616787138883312}},
            '../data/example_dataset_en/samples/corpus-000001.txt': {
                'smmrRE': {'meteor': 0.16609769748922398},
                'sumyLSA': {'meteor': 0.16833631757488907}
            }}
        '''

        return corpusFlat

    def reportTreeToSystemsCorpusFormat(self):
        corpusFlat = self.reportTreeFlattenedByCorpus
        systemsCorpusFormat = self.systemsCorpusFormatter(corpusFlat)
        '''
           {
                'Metric-1':
                    {
                        'smmrRE': [Corpus A Metric-1 Results,
                            Corpus B Metric-1 Results, ...],
                        'sumyLSA': [Corpus A Metric-1 Results,
                            Corpus B Metric-1 Results, ...]
                    }
                'Metric-2':{
                    ...
                }
            }
        '''
        corpora = corpusFlat.keys()

        return systemsCorpusFormat, corpora

    def systemsCorpusFormatter(self, corpFlatForm):

        metrics = self.metrics

        systemsCorpusFormatterByMetric = {}
        for metric in metrics:
            summarizerReports = defaultdict(list)
            '''
                summarizerReports
                {
                 'smmrRE': [corpus a metric score, corpus b metric score],
                 'sumyLSA': [corpus a metric score, corpus b metric score]
                 }
            '''
            for corpus in corpFlatForm:
                corpDict = corpFlatForm[corpus]
                for summarizer in corpDict:
                    summarizerDict = corpDict[summarizer]
                    summarizerReports[summarizer].append(
                        summarizerDict[metric.lower()]
                    )
            systemsCorpusFormatterByMetric[metric.lower()] = summarizerReports

        return systemsCorpusFormatterByMetric


class csvPlotter:

    def __init__(self, summarizers, evaluators, reportTree):
        self.reportTree = reportTree
        self.summarizers = summarizers
        self.evaluators = evaluators
        self.reportTreeReformatter = reportTreeReformatter(
            evaluators, reportTree)

        self.systemsCorpusFormatByMetric, self.corpora = \
            self.reportTreeReformatter\
                .reportTreeToSystemsCorpusFormat()

        self.subHeaderFormats = {
            'rouge': [
                'ROUGE 1-F', 'ROUGE 1-R', 'ROUGE 1-P',
                'ROUGE 2-F', 'ROUGE 2-R', 'ROUGE 2-P',
                'ROUGE L-F', 'ROUGE L-R', 'ROUGE L-P'
            ],
            'pyrouge': [
                'ROUGE 1-F', 'ROUGE 1-R', 'ROUGE 1-P',
                'ROUGE 2-F', 'ROUGE 2-R', 'ROUGE 2-P',
                'ROUGE L-F', 'ROUGE L-R', 'ROUGE L-P'
            ]
        }

        self.paddingSize = {
            'rouge': {
                'left': 0,
                'right': 8
            },
            'pyrouge': {
                'left': 0,
                'right': 8
            }
        }

        self.metricResultReformatters = {
            'rouge': self._reformatRouge,
            'pyrouge': self._reformatPyRouge
        }

    def plot(self):
        '''
        reportTree
        {
            'dataset':{
                'corpusFilePath':{
                    'summarizer':{
                        'metric': report
                    }
                }
            }
        }
        '''
        for dataset in self.reportTree:
            corporaReportMap = self.reportTree[dataset]
            self.plotReportPerCorpora(corporaReportMap)

    def plotMetrics(self):
        allCSVLists = self.constructCSVsFromsystemsCorpusFormat()
        csvFilePaths = self.writeCSVs(allCSVLists)
        self.plotTables(csvFilePaths)

    def writeCSVs(self, CSVs):
        csvFilePaths = []
        metrics = self.evaluators
        for i in range(len(metrics)):
            metric = metrics[i]
            metric = metric.lower()
            csvList = CSVs[i]

            csvFilePaths.append(
                self.writeToCSV(csvList, '{0}_system_corpus'.format(metric))
            )

        return csvFilePaths

    def constructCSVsFromsystemsCorpusFormat(self):
        systemsCorpusFormat = self.systemsCorpusFormatByMetric
        summarizers = self.summarizers
        metrics = self.evaluators
        corpusFlat = self.reportTreeReformatter.reportTreeFlattenedByCorpus
        allCSVLists = []

        corpora = corpusFlat.keys()

        for metric in metrics:
            metric = metric.lower()

            header = self.constructHeader(metric, corpora)
            subHeader = self.constructSubHeader(metric, corpora)

            csvList = [header, subHeader]
            for summarizer in summarizers:
                results = systemsCorpusFormat[metric][summarizer]
                csvLine = [summarizer]
                if metric in self.metricResultReformatters:
                    reformatter = self.metricResultReformatters[metric]
                    reformattedResults = reformatter(results)
                    results = reformattedResults

                csvLine.extend(results)
                csvList.append(csvLine)
            allCSVLists.append(csvList)

        return allCSVLists

    def constructHeader(self, metric, columnTitles, empty=False):
        header = [' '] if not empty else []
        for title in columnTitles:
            header.append(title.upper())
            rightPad = self.paddingSize[metric]['right'] \
                if metric in self.paddingSize else 0
            [header.append(' ') for _ in range(rightPad)]

        return header

    def constructSubHeader(self, metric, titles, empty=False):
        subHeader = ['System'] if not empty else []
        subHeaderCDR = self.subHeaderFormats[metric] \
            if metric in self.subHeaderFormats else [metric.upper()]

        for title in titles:
            subHeader.extend(subHeaderCDR)

        return subHeader

    def _reformatRouge(self, results):

        targetRouges = ['rouge-1', 'rouge-2', 'rouge-l']
        targetScores = ['f', 'r', 'p']

        reformattedResults = [
            result[targetRouge][targetScore]
            for result in results
            for targetRouge in targetRouges
            for targetScore in targetScores
        ]

        return reformattedResults

    def _reformatPyRouge(self, results):
        targetKeys = [
            'rouge_1_f_score', 'rouge_1_recall', 'rouge_1_precision',
            'rouge_2_f_score', 'rouge_2_recall', 'rouge_2_precision',
            'rouge_l_f_score', 'rouge_l_recall', 'rouge_l_precision'
        ]

        reformattedResults = [
            float(result[targetKey])
            for result in results
            for targetKey in targetKeys
        ]

        return reformattedResults

    def plotReportPerCorpora(self, corporaReportMap):
        '''
        corporaReportMap
        {
            'corpusFilePath':{
                'summarizer':{
                    'metric': report
                }
            }
        }
        '''
        for corpus in corporaReportMap:
            corpusReportMap = corporaReportMap[corpus]
            self.plotReportPerCorpus(corpus, corpusReportMap)

    def generateCorpusHeaders(self, metrics):
        header = [' ']
        subHeader = ['System']
        for metric in metrics:
            metric = metric.lower()
            header.extend(
                self.constructHeader(metric, [metric], True))
            subHeader.extend(
                self.constructSubHeader(metric, [metric], True))
        return [header, subHeader]

    def plotReportPerCorpus(self, corpusFilePath, corpusReportMap):
        '''
        corpusReportMap
        {
            'summarizer':{
                'metric': report
            }
        }
        '''
        evaluators = self.evaluators
        evaluators.sort()

        headers = self.generateCorpusHeaders(evaluators)

        csvList = headers

        corpusFileName = os.path.split(corpusFilePath)[1]
        for summarizer in corpusReportMap:
            summarizerReportMap = corpusReportMap[summarizer]
            csvLine = self.summarizerReportMapToCSVFormat(
                summarizer,
                summarizerReportMap)
            csvList.append(csvLine)

        pathToCSV = self.writeToCSV(csvList, corpusFileName)
        self.plotTable(pathToCSV)

    def plotTables(self, filePaths):
        for filePath in filePaths:
            self.plotTable(filePath)

    def plotTable(self, filePath):
        resultsFilePath, resultsFileName = os.path.split(filePath)

        df = pd.read_csv(filePath)
        table = plotly.figure_factory.create_table(df)

        plotFileName = '{0}.html'.format(resultsFileName)
        filename = os.path.join(resultsFilePath, plotFileName)
        plotly.offline.plot(table, filename=filename)

    def summarizerReportMapToCSVFormat(self, summarizer, summarizerReportMap):
        '''
            summarizerReportMap
            {
                'metric': report
            }
        '''
        evaluators = self.evaluators
        evaluators.sort()

        csvLineList = [summarizer]
        for evaluator in evaluators:
            metric = evaluator.lower()
            metricResult = [summarizerReportMap[metric]]
            if metric in self.metricResultReformatters:
                reformatter = self.metricResultReformatters[metric]
                reformattedResult = reformatter(metricResult)
                metricResult = reformattedResult

            csvLineList.extend(metricResult)
        return csvLineList

    def writeToCSV(self, csvList, append=''):
        resultsPath = os.path.join('..', 'results')
        createFolderIfNotExists(resultsPath)

        currDatetime = str(datetime.now())
        pathToResults = os.path.join(
            resultsPath,
            "{0}_results_{1}.csv".format(
                append,
                currDatetime
            )
        )
        with codecs.open(pathToResults, "w") as f:
            writer = csv.writer(f)
            writer.writerows(csvList)
        return pathToResults


class plotFormatter:
    def __init__(self, summarizers, metrics, reportTree):
        self.reportTree = reportTree
        self.metrics = metrics
        self.summarizers = summarizers
        self.defaultFontSize = 12
        self.largeFontSize = 16

        self.pdfPath = os.path.join(
            '..',
            'figs/allFigs_{0}.pdf'
            .format(str(datetime.now())))

        self.reportTreeReformatter = reportTreeReformatter(metrics, reportTree)

        self.systemsCorpusFormatByMetric, self.corpora = \
            self.reportTreeReformatter\
                .reportTreeToSystemsCorpusFormat()
        '''
           {
                'Metric-1':
                    {
                        'smmrRE': [Corpus A Metric-1 Results,
                            Corpus B Metric-1 Results, ...],
                        'sumyLSA': [Corpus A Metric-1 Results,
                            Corpus B Metric-1 Results, ...]
                    }
                'Metric-2':{
                    ...
                }
            }
        '''

        self.cacheSystemsCorpusFormat()
        self.plotMap = {
            'meteor': self.drawNumericPlot('meteor'),
            'bleu': self.drawNumericPlot('bleu'),
            'nist': self.drawNumericPlot('nist'),
            'rouge': self.drawRougePlot,
            'pyrouge': self.drawPyRougePlot
        }

    def cacheSystemsCorpusFormat(self):
        currDatetime = str(datetime.now())
        corpora = self.corpora
        systemsCorpusFormat = self.systemsCorpusFormatByMetric

        systemsCorpusCacheLocation = os.path.join(
            '..', 'cache',
            'systemsCorpusFormat_{0}.txt'.format(currDatetime))

        cacheFolder = os.path.split(systemsCorpusCacheLocation)[0]
        createFolderIfNotExists(cacheFolder)

        with codecs.open(systemsCorpusCacheLocation,
                         'w', 'utf-8') as f:
            f.write(
                '{0}\n{1}'
                .format(list(corpora), json.dumps(systemsCorpusFormat)))

    def drawNumericPlot(self, metricName):
        '''
        Used for any metrics that are sinle integers. Multi-value
        plots require more specialized formatting.
        '''
        metricName = metricName.upper()

        def plot(systemsCorpusFormat, pdf):
            corpora = self.corpora
            corpora = [os.path.split(corp)[1] for corp in corpora]

            plt.figure(figsize=(12, 8))
            ax = plt.subplot(111)
            count = 0

            numCorpora = len(corpora)

            indexes = np.arange(numCorpora)

            numSummarizers = len(systemsCorpusFormat.keys())
            palette = sns.color_palette("Paired", numSummarizers).as_hex()

            arbitraySizeThreshold = 0.8
            barWidth = arbitraySizeThreshold / numSummarizers
            count = 0
            for summarizer in systemsCorpusFormat:
                values = systemsCorpusFormat[summarizer]
                ax.barh(
                    indexes + (barWidth * count),
                    values,
                    barWidth, align='center',
                    label=summarizer, color=palette[count])

                count += 1

            plt.title(
                "{0} Metric Score for each System Sorted by Corpus".
                format(metricName))

            handles, labels = ax.get_legend_handles_labels()

            ax.legend(
                handles=reversed(handles),
                labels=reversed(labels),
                bbox_to_anchor=(1.05, .95))

            plt.ylabel('Corpora')
            plt.xlabel('{0} Score'.format(metricName))

            locations = [
                ind + (1.0 / 2.0 * arbitraySizeThreshold)
                for ind in indexes]
            plt.yticks(locations, corpora)
            sns.despine()

            plt.savefig(
                "../figs/" +
                metricName.upper() +
                "_bar_" +
                str(datetime.now()) +
                '.pdf',
                format='pdf',
                bbox_inches='tight',
                pad_inches=.1)

            pdf.savefig(
                plt.gcf(),
                bbox_inches='tight',
                pad_inches=.1)

        return plot

    def drawPyRougePlot(self, systemsCorpusFormat, pdf):
        scoreTargetsLists = [
            ['rouge_1_f_score', 'rouge_1_recall', 'rouge_1_precision'],
            ['rouge_2_f_score', 'rouge_2_recall', 'rouge_2_precision'],
            ['rouge_l_f_score', 'rouge_l_recall', 'rouge_l_precision']
        ]

        targetTitles = [
            'Pyrouge rouge-1', 'Pyrouge rouge-2', 'Pyrouge rouge-l']
        for i in range(len(scoreTargetsLists)):
            title = targetTitles[i]
            scoreTargets = scoreTargetsLists[i]
            self.drawPyRougeHelper(
                title, scoreTargets, systemsCorpusFormat, pdf)

    def drawPyRougeHelper(self, title, scoreTargets, systemsCorpusFormat, pdf):
        plt.close('all')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)

        fig.suptitle(
            "{0}".format(title.upper()),
            fontsize=self.largeFontSize,
            verticalalignment='top')

        ax4.set_axis_off()
        fig.set_size_inches(16, 8)
        axes = [ax1, ax2, ax3]

        arbitraySizeThreshold = 0.8

        corpora = self.corpora
        corpora = [os.path.split(corp)[1] for corp in corpora]
        numCorpora = len(corpora)
        indexes = np.arange(numCorpora)

        locations = [
            ind + (1.0 / 2.0 * arbitraySizeThreshold)
            for ind in indexes]

        for i in range(len(axes)):
            ax = axes[i]
            scoreTarget = scoreTargets[i]
            self.pyrouge_plot(
                ax,
                scoreTarget, systemsCorpusFormat,
                arbitraySizeThreshold)

            ax.set_yticks(locations, minor=False)
            ax.set_yticklabels(corpora)
            ax.set_ylim(-.2, 3)

        handles, labels = ax3.get_legend_handles_labels()
        ax4.legend(
            handles=reversed(handles),
            labels=reversed(labels),
            bbox_to_anchor=(.50, 1.00))

        sns.despine()

        fig.subplots_adjust(top=0.85)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=2.0)
        plt.savefig(
            "../figs/" +
            title.upper() +
            "_bar_" +
            str(datetime.now()) +
            '.pdf',
            format='pdf',
            bbox_inches='tight',
            pad_inches=.1)

        pdf.savefig(
            plt.gcf(),
            bbox_inches='tight',
            pad_inches=.1)

    def pyrouge_plot(self, ax,
                     scoreTarget, systemsCorpusFormat,
                     arbitraySizeThreshold=0.8):

        ax.set_xlabel(
            '{0} Score'.format(
                scoreTarget.upper()),
            fontsize=self.defaultFontSize)
        ax.set_ylabel('Corpora', fontsize=self.defaultFontSize)

        ax.set_title(
            "{0} Score"
            .format(
                scoreTarget.upper()),
            fontsize=self.defaultFontSize)

        corpora = self.corpora
        numCorpora = len(corpora)
        indexes = np.arange(numCorpora)

        numSummarizers = len(systemsCorpusFormat.keys())
        palette = sns.color_palette("Paired", numSummarizers).as_hex()

        barWidth = arbitraySizeThreshold / numSummarizers
        count = 0
        for summarizer in systemsCorpusFormat:
            values = systemsCorpusFormat[summarizer]
            reformValues = [float(elem[scoreTarget]) for elem in values]
            ax.barh(
                indexes + (barWidth * count),
                reformValues,
                barWidth, align='center',
                label=summarizer, color=palette[count])

            count += 1

    def drawRougePlot(self, systemsCorpusFormat, pdf):
        self.drawRougeFScoreSummary(systemsCorpusFormat, pdf)

        targetRouges = ['rouge-1', 'rouge-2', 'rouge-l']
        for targetRouge in targetRouges:
            self.drawRougeHelper(targetRouge, systemsCorpusFormat, pdf)

    def drawRougeHelper(self, targetRouge, systemsCorpusFormat, pdf):
        plt.close('all')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)

        fig.suptitle(
            "{0}".format(targetRouge.upper()),
            fontsize=self.largeFontSize,
            verticalalignment='top')

        ax4.set_axis_off()
        fig.set_size_inches(16, 8)
        axes = [ax1, ax2, ax3]
        scoreTargets = ['f', 'r', 'p']
        arbitraySizeThreshold = 0.8

        corpora = self.corpora
        corpora = [os.path.split(corp)[1] for corp in corpora]
        numCorpora = len(corpora)
        indexes = np.arange(numCorpora)

        locations = [
            ind + (1.0 / 2.0 * arbitraySizeThreshold)
            for ind in indexes]

        for i in range(len(axes)):
            ax = axes[i]
            scoreTarget = scoreTargets[i]
            self.rouge_plot(
                ax, targetRouge,
                scoreTarget, systemsCorpusFormat,
                arbitraySizeThreshold)

            ax.set_yticks(locations, minor=False)
            ax.set_yticklabels(corpora)
            ax.set_ylim(-.2, 3)

        handles, labels = ax3.get_legend_handles_labels()
        ax4.legend(
            handles=reversed(handles),
            labels=reversed(labels),
            bbox_to_anchor=(.50, 1.00))

        sns.despine()

        fig.subplots_adjust(top=0.85)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=2.0)
        plt.savefig(
            "../figs/" +
            targetRouge.upper() +
            "_bar_" +
            str(datetime.now()) +
            ".pdf",
            format='pdf',
            bbox_inches='tight',
            pad_inches=.1)

        pdf.savefig(
            plt.gcf(),
            bbox_inches='tight',
            pad_inches=.1)

    def drawRougeFScoreSummary(self, systemsCorpusFormat, pdf):
        targetRouges = ['rouge-1', 'rouge-2', 'rouge-l']
        plt.close('all')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)

        fig.suptitle(
            "{0}".format('Rouge F Scores'),
            fontsize=self.largeFontSize,
            verticalalignment='top')

        ax4.set_axis_off()
        fig.set_size_inches(16, 8)
        axes = [ax1, ax2, ax3]

        arbitraySizeThreshold = 0.8

        corpora = self.corpora
        corpora = [os.path.split(corp)[1] for corp in corpora]

        indexes = np.arange(len(corpora))
        locations = [
            ind + (1.0 / 2.0 * arbitraySizeThreshold)
            for ind in indexes]
        for i in range(len(axes)):
            ax = axes[i]
            scoreTarget = 'f'
            targetRouge = targetRouges[i]

            self.rouge_plot(
                ax, targetRouge,
                scoreTarget, systemsCorpusFormat, arbitraySizeThreshold)

            ax.set_yticks(locations, minor=False)
            ax.set_yticklabels(corpora)
            ax.set_ylim(-.2, 3)

        handles, labels = ax3.get_legend_handles_labels()
        ax4.legend(
            handles=reversed(handles),
            labels=reversed(labels),
            bbox_to_anchor=(.50, 1.00))

        sns.despine()

        fig.subplots_adjust(top=0.85)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=2.0)
        plt.savefig(
            "../figs/" +
            'rouge_f_summary' +
            "_bar_" +
            str(datetime.now()) +
            ".pdf",
            format='pdf',
            bbox_inches='tight',
            pad_inches=.1)

        pdf.savefig(
            plt.gcf(),
            bbox_inches='tight',
            pad_inches=.1)

    def rouge_plot(self, ax, targetRouge,
                   scoreTarget, systemsCorpusFormat,
                   arbitraySizeThreshold=0.8):

        ax.set_xlabel(
            '{0} {1} Score'.format(
                'Rouge',
                scoreTarget.upper()),
            fontsize=self.defaultFontSize)
        ax.set_ylabel('Corpora', fontsize=self.defaultFontSize)

        ax.set_title(
            "{0} {1} Score"
            .format(
                targetRouge.upper(),
                scoreTarget.upper()),
            fontsize=self.defaultFontSize)

        corpora = self.corpora
        numCorpora = len(corpora)
        indexes = np.arange(numCorpora)

        numSummarizers = len(systemsCorpusFormat.keys())
        palette = sns.color_palette("Paired", numSummarizers).as_hex()

        barWidth = arbitraySizeThreshold / numSummarizers
        count = 0
        for summarizer in systemsCorpusFormat:
            values = systemsCorpusFormat[summarizer]
            reformValues = [elem[targetRouge][scoreTarget] for elem in values]
            ax.barh(
                indexes + (barWidth * count),
                reformValues,
                barWidth, align='center',
                label=summarizer, color=palette[count])

            count += 1

    def draw(self):
        with PdfPages(self.pdfPath) as pdf:
            systemsCorpusFormatByMetric = self.systemsCorpusFormatByMetric
            for metric in systemsCorpusFormatByMetric:
                method = self.plotMap[metric]
                systemsCorpusFormat = systemsCorpusFormatByMetric[metric]
                method(systemsCorpusFormat, pdf)
