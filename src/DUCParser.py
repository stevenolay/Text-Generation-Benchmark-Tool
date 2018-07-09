import tarfile
import os

import codecs
from collections import OrderedDict, defaultdict
from utils import (
    TemporaryDirectory,
    listFilesInDir
)


class OrderDUC2004:
    def __init__(self, ducFolderPath):
        self.ducFolderPath = ducFolderPath
        with TemporaryDirectory() as tempDir:
            self.modelDirectory = self.initializeModelDirectory(tempDir)
            self.samplesDirectory = self.initializeSamplesDirectory(tempDir)

            self.docIndexMap = OrderedDict()

            self.processDocs()
            self.processModels()

    def initializeSamplesDirectory(self, tempDir):
        # INIT Samples
        samplesDir = os.path.join(tempDir, 'samples')

        os.makedirs(samplesDir)
        DUCSamplesFolderPath = os.path.join(
            self.ducFolderPath,
            "DUC2004_Summarization_Documents.tgz")

        with tarfile.open(DUCSamplesFolderPath) as samplesFiles:
            targetedSamples = [
                tarinfo for tarinfo in samplesFiles.getmembers()
                if tarinfo.name.startswith(
                    "DUC2004_Summarization_Documents/duc2004_testdata/"
                    "tasks1and2/duc2004_tasks1and2_docs/docs"
                )
            ]
            samplesFiles.extractall(members=targetedSamples, path=samplesDir)

        return samplesDir

    def initializeModelDirectory(self, tempDir):
        # INIT Models
        modelDir = os.path.join(tempDir, 'model')
        os.makedirs(modelDir)
        DUCResultsFolderPath = os.path.join(
            self.ducFolderPath,
            "duc2004_results.tar")

        with tarfile.open(DUCResultsFolderPath) as resultsFiles:
            targetedModels = [
                tarinfo for tarinfo in resultsFiles.getmembers()
                if tarinfo.name.startswith(
                    "duc2004_results/ROUGE/"
                    "duc2004.task1.ROUGE.models.tar.gz")
            ]

            resultsFiles.extractall(members=targetedModels, path=modelDir)

        modelTarPath = os.path.join(
            modelDir,
            'duc2004_results/ROUGE/duc2004.task1.ROUGE.models.tar.gz')

        with tarfile.open(modelTarPath) as modelDocs:
            subdirAndFiles = [
                tarinfo for tarinfo in modelDocs.getmembers()
                if tarinfo.name.startswith("./eval")
            ]

            modelDocs.extractall(members=subdirAndFiles, path=modelDir)

        return modelDir

    def makeDir(self, directoryPath):
        try:
            os.mkdir(directoryPath)
        except OSError:
            pass

    def processDocs(self):
        files = listFilesInDir(self.samplesDirectory)
        indexMap = self.docIndexMap
        ducSampleFolderPath = os.path.join(self.ducFolderPath, 'samples')
        self.makeDir(ducSampleFolderPath)

        sampleFolderPath = os.path.join(ducSampleFolderPath, 'DUC-2004.txt')
        with codecs.open(sampleFolderPath, 'w', 'utf-8') as combo:
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
        ducGoldFolderPath = os.path.join(self.ducFolderPath, 'gold')
        self.makeDir(ducGoldFolderPath)

        goldFolderPath = os.path.join(ducGoldFolderPath, 'DUC-2004_gold.txt')
        with codecs.open(goldFolderPath, 'w', 'utf-8') as combo:
            if not lineMap:
                return

            for identifier in lineMap:
                filePath = fileIdentifierMap[identifier][0]
                with codecs.open(filePath, 'r', 'utf-8') as f:
                    text = f.readlines()
                    targetText = ''.join(text)
                    targetText = targetText.replace('\n', '')
                    combo.write(targetText)
                    combo.write('\n')
            combo.seek(-1, os.SEEK_END)
            combo.truncate()  # Remove trailing new line
