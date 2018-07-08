import tarfile
import os

import codecs
from collections import OrderedDict, defaultdict
from utils import (
    TemporaryDirectory,
    list_files
)


class OrderDUC2004:
    def __init__(self):
        with TemporaryDirectory() as temp_dir:
            self.modelDirectory = self.initializeModelDirectory(temp_dir)
            self.samplesDirectory = self.initializeSamplesDirectory(temp_dir)

            self.docIndexMap = OrderedDict()

            self.processDocs()
            self.processModels()

    def initializeSamplesDirectory(self, temp_dir):
        # INIT Samples
        samples_dir = os.path.join(temp_dir, 'samples')
        os.makedirs(samples_dir)
        DUCSamplesFolderPath = "../data/DUC/DUC2004_" \
            "Summarization_Documents.tgz"

        with tarfile.open(DUCSamplesFolderPath) as samplesFiles:
            targetedSamples = [
                tarinfo for tarinfo in samplesFiles.getmembers()
                if tarinfo.name.startswith(
                    "DUC2004_Summarization_Documents/duc2004_testdata/"
                    "tasks1and2/duc2004_tasks1and2_docs/docs"
                )
            ]
            samplesFiles.extractall(members=targetedSamples, path=samples_dir)

        return samples_dir

    def initializeModelDirectory(self, temp_dir):
        # INIT Models
        model_dir = os.path.join(temp_dir, 'model')
        os.makedirs(model_dir)
        DUCResultsFolderPath = "../data/DUC/duc2004_results.tar"
        with tarfile.open(DUCResultsFolderPath) as resultsFiles:
            targetedModels = [
                tarinfo for tarinfo in resultsFiles.getmembers()
                if tarinfo.name.startswith(
                    "duc2004_results/ROUGE/"
                    "duc2004.task1.ROUGE.models.tar.gz"
                )
            ]

            resultsFiles.extractall(members=targetedModels, path=model_dir)

        modelTarPath = os.path.join(
            model_dir,
            'duc2004_results/ROUGE/duc2004.task1.ROUGE.models.tar.gz')

        with tarfile.open(modelTarPath) as modelDocs:
            subdir_and_files = [
                tarinfo for tarinfo in modelDocs.getmembers()
                if tarinfo.name.startswith("./eval")
            ]

            modelDocs.extractall(members=subdir_and_files, path=model_dir)

        return model_dir

    def makeDir(self, directoryPath):
        try:
            os.mkdir(directoryPath)
        except OSError:
            pass

    def processDocs(self):
        files = list_files(self.samplesDirectory)
        indexMap = self.docIndexMap

        self.makeDir('../data/DUC/samples')

        with codecs.open(
            '../data/DUC/samples/DUC-2004.txt', 'w', 'utf-8'
        ) as combo:
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
        modelFiles = list_files(modelDirectory)

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

        self.makeDir('../data/DUC/gold')

        with codecs.open(
            '../data/DUC/gold/DUC-2004_gold.txt', 'w', 'utf-8'
        ) as combo:
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
