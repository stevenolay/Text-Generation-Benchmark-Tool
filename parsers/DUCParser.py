import tarfile
import os
import tempfile
import contextlib
import shutil
import codecs
import json
from collections import OrderedDict, defaultdict


class OrderDUC2004:
    def __init__(self, summarizationDocsTarPath, resultsTarPath):
        self.docPath = summarizationDocsTarPath
        self.resultsPath = resultsTarPath
        with TemporaryDirectory() as tempDir:
            self.modelDirectory = self.initializeModelDirectory(tempDir)
            self.resultsDirectory = self.initializeSamplesDirectory(tempDir)

            self.docIndexMap = OrderedDict()

            self.processDocs()
            self.processModels()

    def initializeSamplesDirectory(self, tempDir):
        # INIT Samples
        docsDir = os.path.join(tempDir, 'docs')
        os.makedirs(docsDir)

        DUCDocsFolderPath = self.docPath

        with tarfile.open(DUCDocsFolderPath) as docFiles:
            targetedDocs = [
                tarinfo for tarinfo in docFiles.getmembers()
                if tarinfo.name.startswith(
                    "DUC2004_Summarization_Documents/duc2004_testdata/"
                    "tasks1and2/duc2004_tasks1and2_docs/docs"
                )
            ]
            docFiles.extractall(members=targetedDocs, path=docsDir)

        return docsDir

    def initializeModelDirectory(self, tempDir):
        # INIT Models
        resultsDir = os.path.join(tempDir, 'model')
        os.makedirs(resultsDir)

        DUCResultsTarFilePath = self.resultsPath
        with tarfile.open(DUCResultsTarFilePath) as resultsFiles:
            targetedModels = [
                tarinfo for tarinfo in resultsFiles.getmembers()
                if tarinfo.name.startswith(
                    "duc2004_results/ROUGE/"
                    "duc2004.task1.ROUGE.models.tar.gz")
            ]

            resultsFiles.extractall(members=targetedModels, path=resultsDir)

        resultsTarPath = os.path.join(
            resultsDir,
            'duc2004_results/ROUGE/duc2004.task1.ROUGE.models.tar.gz')

        with tarfile.open(resultsTarPath) as resultsDocs:
            subdirAndFiles = [
                tarinfo for tarinfo in resultsDocs.getmembers()
                if tarinfo.name.startswith("./eval")
            ]

            resultsDocs.extractall(members=subdirAndFiles, path=resultsDir)

        return resultsDir

    def makeDir(self, directoryPath):
        try:
            os.makedirs(directoryPath)
        except OSError:
            pass

    def processDocs(self):
        files = listFilesInDir(self.resultsDirectory)
        indexMap = self.docIndexMap
        ducSampleFolderPath = './DUC/samples'
        self.makeDir(ducSampleFolderPath)

        ducSampleFilePath = os.path.join(ducSampleFolderPath, 'DUC-2004.txt')
        with codecs.open(ducSampleFilePath, 'w', 'utf-8') as combo:
            index = 0
            if not files:
                return
            for file in files:
                fileName = os.path.basename(file)
                folderName = os.path.basename(os.path.dirname(file))
                folderName = folderName[0:len(folderName) - 1].upper()

                commonIdentifier = (folderName + fileName).replace('.', '')

                indexMap[commonIdentifier] = index
                with codecs.open(file, 'r', 'utf-8') as f:
                    text = f.readlines()
                    indices = [
                        i for i, x in enumerate(text)
                        if x == "<TEXT>\n" or x == "</TEXT>\n"
                    ]
                    targetTextList = text[indices[0] + 1: indices[1]]
                    targetText = ''.join(targetTextList)
                    targetText = targetText.replace('\n', '')
                    combo.write(targetText)
                    combo.write('\n')
                index += 1

            combo.seek(-1, os.SEEK_END)
            combo.truncate()  # Remove trailing new line
        return indexMap

    def generateCommonIdentifierFromModel(self, file):
        fileName = os.path.basename(file)
        fileNameList = fileName.split('.')
        identifier = fileNameList[0] + fileNameList[5] + fileNameList[6]

        return identifier

    def mapModelsToCommonIdentifier(self):
        modelDirectory = os.path.join(self.modelDirectory, 'eval')
        modelFiles = listFilesInDir(modelDirectory)

        modelIndetifierMap = defaultdict(list)
        for file in modelFiles:
            identifier = self.generateCommonIdentifierFromModel(file)
            modelIndetifierMap[identifier].append(file)

        return modelIndetifierMap

    def processModels(self):
        lineMap = self.docIndexMap  # This is ordered by insert.
        # so it will be an index to index match upon iteration.
        fileIdentifierMap = self.mapModelsToCommonIdentifier()
        assert len(lineMap.keys()) == len(fileIdentifierMap.keys())
        # expect to be the same length
        ducGoldFolderPath = 'DUC/gold'
        self.makeDir(ducGoldFolderPath)

        ducGoldFilePath = os.path.join(ducGoldFolderPath, 'DUC-2004_gold.txt')
        with codecs.open(ducGoldFilePath, 'w', 'utf-8') as combo:
            if not lineMap:
                return

            for identifier in lineMap:
                filePaths = fileIdentifierMap[identifier]
                references = []
                for filePath in filePaths:
                    with codecs.open(filePath, 'r', 'utf-8') as f:
                        text = f.readlines()
                        targetText = ''.join(text)
                        targetText = targetText.replace('\n', '')
                        references.append(targetText)
                referencesJSON = {"references": references}
                combo.write(json.dumps(referencesJSON))
                combo.write('\n')
            combo.seek(-1, os.SEEK_END)
            combo.truncate()  # Remove trailing new line


# Helper Functions #
@contextlib.contextmanager
def TemporaryDirectory(*args, **kwargs):
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)


def listFilesInDir(dir):
    r = []
    subdirs = [x[0] for x in os.walk(dir)]
    for subdir in subdirs:
        files = os.walk(subdir).next()[2]
        if (len(files) > 0):
            for file in files:
                r.append(subdir + "/" + file)
    return r


OrderDUC2004(
    '../data/DUC/DUC2004_Summarization_Documents.tgz',
    '../data/DUC/duc2004_results.tar')
