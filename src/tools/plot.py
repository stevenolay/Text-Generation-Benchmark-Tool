from .utils import createFolderIfNotExists
from datetime import datetime
import plotly.figure_factory
import plotly.offline
import json

import os
import csv
import codecs
from collections import defaultdict
from datetime import datetime

import pandas as pd

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages

# The PDF document
# pdf_pages = PdfPages('my-fancy-document.pdf')

import seaborn as sns
sns.set_context("talk")
sns.set_style("white")

def plotTables(files):
    for file in files:
        plotTable(file)


def plotTable(file):
    resultsFilePath, resultsFileName = os.path.split(file)

    df = pd.read_csv(file)
    table = plotly.figure_factory.create_table(df)

    plotFileName = '{0}.html'.format(resultsFileName)
    filename = os.path.join(resultsFilePath, plotFileName)
    plotly.offline.plot(table, filename=filename)


'''
plotTable('results.csv')
"https://raw.githubusercontent.com/plotly/datasets/master/school_earnings.csv"
'''


def plotSystemsCorpusPerMetric(summarizers, metrics, reportTree):
    '''
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

    systemsCorpusFormat = systemsCorpusFormatter(
        metrics, corpusFlat)

    corpora = corpusFlat.keys()

    print((corpora, systemsCorpusFormat))

    currDatetime = str(datetime.now())
    with codecs.open('{0}_systemsCorpusFormat.txt'.format(currDatetime),
                     'w', 'utf-8') as f:
        f.write('{0}\n{1}'.format(corpora, json.dumps(systemsCorpusFormat)))

    with codecs.open('{0}_report_tree.txt'.format(currDatetime),
                     'w', 'utf-8') as f:
        f.write('{0}'.format(reportTree))


    #pF = plotFormatter(corpora, systemsCorpusFormat)
    #pF.draw()
    '''
    allCSVs = constructCSVsFromsystemsCorpusFormat(
        metrics, summarizers,
        corpusFlat, systemsCorpusFormat)
    csvFiles = []
    for metric in metrics:
        metric = metric.lower()
        csvFiles.extend([
            writeToCSV('{0}_system_corpus'.format(metric), csvList)
            for csvList in allCSVs
        ])

    plotTables(csvFiles)
    '''


def writeToCSV(name, csvList):
    resultsPath = os.path.join('..', 'results')
    createFolderIfNotExists(resultsPath)

    currDatetime = str(datetime.now())
    pathToResults = os.path.join(
        resultsPath,
        "{0}_results_{1}.csv".format(
            name,
            currDatetime
        )
    )
    with codecs.open(pathToResults, "w") as f:
        writer = csv.writer(f)
        writer.writerows(csvList)
    return pathToResults


def constructCSVsFromsystemsCorpusFormat(metrics, summarizers,
                                         corpusFlat, systemsCorpusFormat):
    allCSVLists = []

    header = ['System']
    header.extend(corpusFlat.keys())

    for metric in metrics:
        metric = metric.lower()
        csvList = [header]
        for summarizer in summarizers:
            results = systemsCorpusFormat[metric][summarizer]
            csvLine = [summarizer]
            csvLine.extend(results)
            csvList.append(csvLine)
        allCSVLists.append(csvList)

    return allCSVLists


def systemsCorpusFormatter(metrics, corpFlatForm):
    '''
    corpFlatForm = {
    '../data/DUC_multi/samples/DUC-2004.txt': {
        'smmrRE': {'meteor': 0.1685136779914727},
        'sumyLSA': {'meteor': 0.15616787138883312}},
    '../data/example_dataset_en/samples/corpus-000001.txt': {
        'smmrRE': {'meteor': 0.16609769748922398},
        'sumyLSA': {'meteor': 0.16833631757488907}
    }}
    '''
    systemsCorpusFormatterByMetric = {}
    for metric in metrics:
        summarizerReports = defaultdict(list)
        #  summarizerReports = {
        #   'smmrRE': [corpus a metric score, corpus b metric score],
        #   'sumyLSA': [corpus a metric score, corpus b metric score]}
        for corpus in corpFlatForm:
            corpDict = corpFlatForm[corpus]
            for summarizer in corpDict:
                summarizerDict = corpDict[summarizer]
                summarizerReports[summarizer].append(
                    summarizerDict[metric.lower()]
                )
        systemsCorpusFormatterByMetric[metric.lower()] = summarizerReports

    return systemsCorpusFormatterByMetric


# make_rectangle_figure(6.5, save=True)
#{'meteor': defaultdict(<class 'list'>, {'smmrRE': [0.1685136779914727, 0.16609769748922398], 'sumyLSA': [0.15616787138883312, 0.16833631757488907]})}

class plotFormatter:
    def __init__(self, corpora, systemsCorpusFormatByMetric):
        self.defaultFontSize = 12
        self.largeFontSize = 16
        self.systemsCorpusFormatByMetric = systemsCorpusFormatByMetric
        self.corpora = corpora
        self.plotMap = {
            'meteor': self.drawMeteorPlot,
            'rouge': self.drawRougePlot
        }

    def drawMeteorPlot(self, systemsCorpusFormat):
        corpora = self.corpora
        corpora = [os.path.split(corp)[1] for corp in corpora]


        plt.figure(figsize=(12, 8))
        ax = plt.subplot(111)
        count = 0

        numCorpora = len(corpora)

        indexes = np.arange(numCorpora)

        numSummarizers = len(systemsCorpusFormat.keys())
        palette = sns.color_palette("Paired", numSummarizers).as_hex()
        #  palette = sns.diverging_palette(
        #    10, 220, sep=80, n=numSummarizers).as_hex()

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
            format('METEOR'))

        handles, labels = ax.get_legend_handles_labels()

        ax.legend(
            handles=reversed(handles),
            labels=reversed(labels),
            bbox_to_anchor=(1.05, .95))

        plt.ylabel('Corpora')
        plt.xlabel('{0} Score'.format('METEOR'))

        locations = [
            ind + (1.0 / 2.0 * arbitraySizeThreshold)
            for ind in indexes]
        plt.yticks(locations, corpora)
        sns.despine()
        plt.show()

    def drawRougePlot(self, systemsCorpusFormat):
        targetRouges = ['rouge-1', 'rouge-2', 'rouge-l']
        for targetRouge in targetRouges:
            self.drawRougeHelper(targetRouge, systemsCorpusFormat)

    def drawRougeHelper(self, targetRouge, systemsCorpusFormat):
        plt.close('all')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)

        fig.suptitle(
            "{0}".format(targetRouge.upper()),
            fontsize=self.largeFontSize,
            verticalalignment='top')

        ax4.set_axis_off()
        fig.set_size_inches(16, 8)
        axes = [ax1, ax2, ax3]
        scoreTargets = ['p', 'r', 'f']
        arbitraySizeThreshold = 0.8

        corpora = self.corpora
        corpora = [os.path.split(corp)[1] for corp in corpora]

        indexes = np.arange(len(corpora))
        locations = [
            ind + (1.0 / 2.0 * arbitraySizeThreshold)
            for ind in indexes]

        for i in range(len(axes)):
            ax = axes[i]
            scoreTarget = scoreTargets[i]
            self.rouge_plot(
                ax, targetRouge, scoreTarget,
                systemsCorpusFormat, arbitraySizeThreshold)
            ax.set_yticks(locations, minor=False)
            ax.set_yticklabels(corpora)

        handles, labels = ax3.get_legend_handles_labels()
        ax4.legend(
            handles=reversed(handles),
            labels=reversed(labels),
            bbox_to_anchor=(.50, 1.00))

        sns.despine()
        #  plt.subplots_adjust(left=-.5, wspace=3, top=0.8)
        fig.subplots_adjust(top=0.85)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=2.0)
        plt.show()

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
            "{0} {1} Metric Score for each System Sorted by Corpus"
            .format('Rouge', scoreTarget.upper()),
            fontsize=self.defaultFontSize)

        corpora = self.corpora
        numCorpora = len(corpora)
        indexes = np.arange(numCorpora)

        numSummarizers = len(systemsCorpusFormat.keys())
        palette = sns.color_palette("Paired", numSummarizers).as_hex()
        #  palette = sns.diverging_palette(
        #    10, 220, sep=80, n=numSummarizers).as_hex()

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
        systemsCorpusFormatByMetric = self.systemsCorpusFormatByMetric
        for metric in systemsCorpusFormatByMetric:
            method = self.plotMap[metric]
            systemsCorpusFormat = systemsCorpusFormatByMetric[metric]
            method(systemsCorpusFormat)

'''
plt.savefig("figs/illustrator/"+str(value)+"bar.pdf",
            format='pdf',
            bbox_inches='tight',
            pad_inches=0)
'''
'''
pF =plotFormatter(
    [
    '../data/DUC_multi/samples/DUC-2004.txt',
    '../data/Arxiv/samples/arxiv.txt',
    '../data/example_dataset_en/samples/corpus-000001.txt'],
    {u'meteor': {
        u'sumyLexRank': [0.17203705742313663, 0.21840406613741767, 0.14855167299570654],
        u'sumyLSA': [0.15616787138883312, 0.152766100785992, 0.16833631757488907],
        u'sumyTextRank': [0.16980083900455187, 0.1888387384808625, 0.15858024787137026],
        u'sumyEdmundson': [0.1956148983199971, 0.12292734980275215, 0.1476787043392584],
        u'sumyRandom': [0.13857786647813775, 0.1248674197755125, 0.1197064243802743],
        u'sumyEdmundsonCue': [0.19833097111082026, 0.16911710161901042, 0.14176048584931464],
        u'sumyKL': [0.15326565201643147, 0.2193024788178896, 0.15042396210074477],
        u'sumySumBasic': [0.1575531372308491, 0.11157013994790659, 0.12587489064242327],
        u'smmrRE': [0.1685136779914727, 0.19024399080570006, 0.16609769748922398],
        u'sumyLuhn': [0.16912761372418628, 0.23247344814596654, 0.14605105711875677],
        u'sumyEdmundsonKey': [0.19838139546599212, 0.16911710161901042, 0.14176048584931464],
        u'sumyEdmundsonLocation': [0.19542538802798984, 0.12292734980275215, 0.1476787043392584],
        u'sumyEdmundsonTitle': [0.19838139546599212, 0.16911710161901042, 0.14176048584931464]}})
'''
'''
pF=plotFormatter(['../data/DUC_multi/samples/DUC-2004.txt', '../data/Arxiv/samples/arxiv.txt', '../data/example_dataset_en/samples/corpus-000001.txt'],
                  {u'rouge': {u'sumyLexRank': [
                      {'rouge-l': {'p': 0.062310975535037665, 'r': 0.34236965538546316, 'f': 0.06431407902883031},
                       'rouge-2': {'p': 0.011479803989045544, 'r': 0.08267064116439136, 'f': 0.01986196790910434},
                       'rouge-1': {'p': 0.06811987707778612, 'r': 0.37402597198553034, 'f': 0.11398468493656251}},
                      {'rouge-l': {'p': 0.19158878504672897, 'r': 0.5061728395061729, 'f': 0.20777019653383716},
                       'rouge-2': {'p': 0.07105263157894737, 'r': 0.2231404958677686, 'f': 0.10778442747399425},
                       'rouge-1': {'p': 0.205607476635514, 'r': 0.5432098765432098, 'f': 0.2983050807620799}},
                      {'rouge-l': {'p': 0.1821106111278025, 'r': 0.34127778996077796, 'f': 0.20106345297287798},
                       'rouge-2': {'p': 0.043551518483840874, 'r': 0.0997484902774373, 'f': 0.060005542114664405},
                       'rouge-1': {'p': 0.2126630102613947, 'r': 0.4011283025026822, 'f': 0.2742249989693121}}],
                              u'sumyLSA': [{'rouge-l': {'p': 0.05267246036824723, 'r': 0.3621334806533328, 'f': 0.05381617860427389}, 'rouge-2': {'p': 0.009626402694637597, 'r': 0.08397972860472884, 'f': 0.01703011055177792}, 'rouge-1': {'p': 0.05768199060361813, 'r': 0.39626337020822294, 'f': 0.09984001874509997}}, {'rouge-l': {'p': 0.17721518987341772, 'r': 0.345679012345679, 'f': 0.19721821110264423}, 'rouge-2': {'p': 0.032, 'r': 0.06611570247933884, 'f': 0.04312668024062643}, 'rouge-1': {'p': 0.20253164556962025, 'r': 0.3950617283950617, 'f': 0.26778242229722876}}, {'rouge-l': {'p': 0.17259338051619696, 'r': 0.41869983676344996, 'f': 0.188873423793935}, 'rouge-2': {'p': 0.05330704626099134, 'r': 0.1520373764708934, 'f': 0.07788779048274065}, 'rouge-1': {'p': 0.199664442254444, 'r': 0.49227243830601813, 'f': 0.28047743768920097}}], u'sumyTextRank': [{'rouge-l': {'p': 0.06208591665791414, 'r': 0.391725759208112, 'f': 0.06358412990442815}, 'rouge-2': {'p': 0.01226412891226047, 'r': 0.10187491744366768, 'f': 0.02159315814123261}, 'rouge-1': {'p': 0.06797547706269233, 'r': 0.42832639260249594, 'f': 0.11602795362691773}}, {'rouge-l': {'p': 0.14334470989761092, 'r': 0.5185185185185185, 'f': 0.15110726419130258}, 'rouge-2': {'p': 0.04631217838765009, 'r': 0.2231404958677686, 'f': 0.07670454260786588}, 'rouge-1': {'p': 0.15017064846416384, 'r': 0.5432098765432098, 'f': 0.23529411425362468}}, {'rouge-l': {'p': 0.1710614547820745, 'r': 0.36903413993716727, 'f': 0.18809383756905143}, 'rouge-2': {'p': 0.04760107266170253, 'r': 0.12705754821690438, 'f': 0.06831720649772609}, 'rouge-1': {'p': 0.20289083479898365, 'r': 0.43853142791980765, 'f': 0.2729797657738746}}], u'sumyEdmundson': [{'rouge-l': {'p': 0.06929954918127461, 'r': 0.3975340754017216, 'f': 0.07135668046788086}, 'rouge-2': {'p': 0.016022506276275675, 'r': 0.11716694347319367, 'f': 0.027830474887843754}, 'rouge-1': {'p': 0.07615077591342549, 'r': 0.43588213657257746, 'f': 0.12833039633065188}}, {'rouge-l': {'p': 0.323943661971831, 'r': 0.2839506172839506, 'f': 0.30004542633252307}, 'rouge-2': {'p': 0.1134020618556701, 'r': 0.09090909090909091, 'f': 0.10091742625326175}, 'rouge-1': {'p': 0.36619718309859156, 'r': 0.32098765432098764, 'f': 0.342105258179536}}, {'rouge-l': {'p': 0.2047522877696857, 'r': 0.32485499970012005, 'f': 0.219348328638022}, 'rouge-2': {'p': 0.06073148940261474, 'r': 0.10882109641288766, 'f': 0.07441601111661572}, 'rouge-1': {'p': 0.22992289618373393, 'r': 0.3638708361887915, 'f': 0.2748376333351687}}], u'sumyRandom': [{'rouge-l': {'p': 0.051416041873985005, 'r': 0.2624877719910799, 'f': 0.05327745656624707}, 'rouge-2': {'p': 0.006874103426664802, 'r': 0.043293306693306804, 'f': 0.011531990012983393}, 'rouge-1': {'p': 0.05598186083890121, 'r': 0.28560964178794973, 'f': 0.09237106650268506}}, {'rouge-l': {'p': 0.168, 'r': 0.25925925925925924, 'f': 0.18752007392771747}, 'rouge-2': {'p': 0.03414634146341464, 'r': 0.05785123966942149, 'f': 0.04294478060803996}, 'rouge-1': {'p': 0.184, 'r': 0.2839506172839506, 'f': 0.22330096610189473}}, {'rouge-l': {'p': 0.15588799906597986, 'r': 0.29648774052347965, 'f': 0.17060618353298276}, 'rouge-2': {'p': 0.02285803098734442, 'r': 0.056161446080800904, 'f': 0.032032871404950224}, 'rouge-1': {'p': 0.18633581907545413, 'r': 0.36471766157548186, 'f': 0.239688361093266}}], u'sumyEdmundsonCue': [{'rouge-l': {'p': 0.0716937664206703, 'r': 0.42434501119795176, 'f': 0.07369696766595044}, 'rouge-2': {'p': 0.01606113792747787, 'r': 0.12435751401376424, 'f': 0.028110840816599807}, 'rouge-1': {'p': 0.07813581728842468, 'r': 0.4624322933602349, 'f': 0.13237448596790197}}, {'rouge-l': {'p': 0.313953488372093, 'r': 0.3333333333333333, 'f': 0.3227751334687374}, 'rouge-2': {'p': 0.112, 'r': 0.11570247933884298, 'f': 0.11382113321270432}, 'rouge-1': {'p': 0.36046511627906974, 'r': 0.38271604938271603, 'f': 0.3712574800344222}}, {'rouge-l': {'p': 0.18256572588469142, 'r': 0.32635428219117707, 'f': 0.20067027075104008}, 'rouge-2': {'p': 0.04960273043199482, 'r': 0.10060517330383577, 'f': 0.06549791893758274}, 'rouge-1': {'p': 0.21059422675801986, 'r': 0.3742477275507787, 'f': 0.26539030933356217}}], u'sumyKL': [{'rouge-l': {'p': 0.052543366217288785, 'r': 0.32609531881516995, 'f': 0.053951344402222066}, 'rouge-2': {'p': 0.009084472823120252, 'r': 0.07141351703851723, 'f': 0.01585728658413391}, 'rouge-1': {'p': 0.05764264917232322, 'r': 0.3574909086420098, 'f': 0.09816099869782129}}, {'rouge-l': {'p': 0.23783783783783785, 'r': 0.5432098765432098, 'f': 0.2614842987079537}, 'rouge-2': {'p': 0.07605633802816901, 'r': 0.2231404958677686, 'f': 0.11344537435959692}, 'rouge-1': {'p': 0.24324324324324326, 'r': 0.5555555555555556, 'f': 0.338345860425971}}, {'rouge-l': {'p': 0.1637835065392341, 'r': 0.36011503490025265, 'f': 0.17979526965411083}, 'rouge-2': {'p': 0.04240171712229091, 'r': 0.11962150169647547, 'f': 0.06152091481850084}, 'rouge-1': {'p': 0.19370000039513122, 'r': 0.43154487407627323, 'f': 0.26279197337226}}], u'sumySumBasic': [{'rouge-l': {'p': 0.0631084182153705, 'r': 0.26749309709897867, 'f': 0.06623488146942985}, 'rouge-2': {'p': 0.009273072802915255, 'r': 0.050326839826839956, 'f': 0.01535681186456389}, 'rouge-1': {'p': 0.06899139636540207, 'r': 0.29323598080840685, 'f': 0.10982712601334568}}, {'rouge-l': {'p': 0.21518987341772153, 'r': 0.20987654320987653, 'f': 0.21243362486287085}, 'rouge-2': {'p': 0.0625, 'r': 0.05785123966942149, 'f': 0.06008583191733174}, 'rouge-1': {'p': 0.25316455696202533, 'r': 0.24691358024691357, 'f': 0.24999999500078132}}, {'rouge-l': {'p': 0.21792668391100448, 'r': 0.25879176886196303, 'f': 0.1960111509584935}, 'rouge-2': {'p': 0.049185618290667775, 'r': 0.06671140638144966, 'f': 0.05141214748550799}, 'rouge-1': {'p': 0.27383719132848056, 'r': 0.33325571342292587, 'f': 0.27995153948243795}}], u'smmrRE': [{'rouge-l': {'p': 0.05940362682088171, 'r': 0.4012424708869554, 'f': 0.060746855751196815}, 'rouge-2': {'p': 0.01171848188890427, 'r': 0.10458683885558906, 'f': 0.02079707310941091}, 'rouge-1': {'p': 0.06485359325330607, 'r': 0.43793624031197587, 'f': 0.11192301652711147}}, {'rouge-l': {'p': 0.14334470989761092, 'r': 0.5185185185185185, 'f': 0.15110726419130258}, 'rouge-2': {'p': 0.04631217838765009, 'r': 0.2231404958677686, 'f': 0.07670454260786588}, 'rouge-1': {'p': 0.15017064846416384, 'r': 0.5432098765432098, 'f': 0.23529411425362468}}, {'rouge-l': {'p': 0.17036829683502555, 'r': 0.38098789555494456, 'f': 0.18705262892193386}, 'rouge-2': {'p': 0.0533036546715475, 'r': 0.13647174513110127, 'f': 0.07489557433659837}, 'rouge-1': {'p': 0.1987542031882427, 'r': 0.45676395320447755, 'f': 0.2723886041798843}}], u'sumyLuhn': [{'rouge-l': {'p': 0.06137045265156413, 'r': 0.3755141649608551, 'f': 0.06299014712412906}, 'rouge-2': {'p': 0.011901022485050431, 'r': 0.0955218760406262, 'f': 0.020889254335583047}, 'rouge-1': {'p': 0.06700978180749592, 'r': 0.4095613504142913, 'f': 0.11411667291907868}}, {'rouge-l': {'p': 0.208955223880597, 'r': 0.5185185185185185, 'f': 0.22796976713657122}, 'rouge-2': {'p': 0.08426966292134831, 'r': 0.24793388429752067, 'f': 0.12578615973559426}, 'rouge-1': {'p': 0.22885572139303484, 'r': 0.5679012345679012, 'f': 0.32624113065716015}}, {'rouge-l': {'p': 0.17437940324168935, 'r': 0.3738501255831594, 'f': 0.1918336129589183}, 'rouge-2': {'p': 0.039921073908822956, 'r': 0.1001811520064864, 'f': 0.05629713469714287}, 'rouge-1': {'p': 0.2047133892666906, 'r': 0.4396377879270473, 'f': 0.274636884880068}}], u'sumyEdmundsonKey': [{'rouge-l': {'p': 0.07169208291898678, 'r': 0.424190844531285, 'f': 0.0736970414125432}, 'rouge-2': {'p': 0.01606379661807275, 'r': 0.12433153998779022, 'f': 0.028113661652491895}, 'rouge-1': {'p': 0.0781476018002092, 'r': 0.4623197933602349, 'f': 0.13238356869427778}}, {'rouge-l': {'p': 0.313953488372093, 'r': 0.3333333333333333, 'f': 0.3227751334687374}, 'rouge-2': {'p': 0.112, 'r': 0.11570247933884298, 'f': 0.11382113321270432}, 'rouge-1': {'p': 0.36046511627906974, 'r': 0.38271604938271603, 'f': 0.3712574800344222}}, {'rouge-l': {'p': 0.18256572588469142, 'r': 0.32635428219117707, 'f': 0.20067027075104008}, 'rouge-2': {'p': 0.04960273043199482, 'r': 0.10060517330383577, 'f': 0.06549791893758274}, 'rouge-1': {'p': 0.21059422675801986, 'r': 0.3742477275507787, 'f': 0.26539030933356217}}], u'sumyEdmundsonLocation': [{'rouge-l': {'p': 0.06925420604401973, 'r': 0.39710074206838825, 'f': 0.07131458286960858}, 'rouge-2': {'p': 0.016026388263853313, 'r': 0.1170955149017651, 'f': 0.02782908826371361}, 'rouge-1': {'p': 0.07609562885460197, 'r': 0.43540713657257746, 'f': 0.12821902163446822}}, {'rouge-l': {'p': 0.323943661971831, 'r': 0.2839506172839506, 'f': 0.30004542633252307}, 'rouge-2': {'p': 0.1134020618556701, 'r': 0.09090909090909091, 'f': 0.10091742625326175}, 'rouge-1': {'p': 0.36619718309859156, 'r': 0.32098765432098764, 'f': 0.342105258179536}}, {'rouge-l': {'p': 0.2047522877696857, 'r': 0.32485499970012005, 'f': 0.219348328638022}, 'rouge-2': {'p': 0.06073148940261474, 'r': 0.10882109641288766, 'f': 0.07441601111661572},
'rouge-1': {'p': 0.22992289618373393, 'r': 0.3638708361887915, 'f': 0.2748376333351687}}], u'sumyEdmundsonTitle': [{'rouge-l': {'p': 0.07169208291898678, 'r': 0.424190844531285, 'f': 0.0736970414125432}, 'rouge-2': {'p': 0.01606379661807275, 'r': 0.12433153998779022, 'f': 0.028113661652491895}, 'rouge-1': {'p': 0.0781476018002092, 'r': 0.4623197933602349, 'f': 0.13238356869427778}}, {'rouge-l': {'p': 0.313953488372093, 'r': 0.3333333333333333, 'f': 0.3227751334687374}, 'rouge-2': {'p': 0.112, 'r': 0.11570247933884298, 'f': 0.11382113321270432}, 'rouge-1': {'p': 0.36046511627906974, 'r': 0.38271604938271603, 'f': 0.3712574800344222}}, {'rouge-l': {'p': 0.18256572588469142, 'r': 0.32635428219117707, 'f': 0.20067027075104008}, 'rouge-2': {'p': 0.04960273043199482, 'r': 0.10060517330383577, 'f': 0.06549791893758274}, 'rouge-1': {'p': 0.21059422675801986, 'r': 0.3742477275507787, 'f': 0.26539030933356217}}]}})

pF.draw()
'''
