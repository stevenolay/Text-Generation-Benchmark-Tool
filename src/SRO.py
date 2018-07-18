import codecs
import json
'''
import xml.parsers.expat
parser = xml.parsers.expat.ParserCreate()
parser.ParseFile(open('path.xml', 'r'))
'''


class SummaryReaderObject:
    def __init__(self, summaryFilePath, goldFilePath, **kwargs):
        self.kwargs = kwargs
        self.summaryFilePath = summaryFilePath
        self.goldFilePath = goldFilePath

        self.summariesFile = codecs.open(summaryFilePath, 'rb+', 'utf-8')
        self.goldFile = codecs.open(goldFilePath, 'rb+', 'utf-8')

        self.goldFormat = kwargs['goldFormat'] if ('goldFormat' in kwargs) \
            else self._inferFormat()
        self.kwargs['goldFormat'] = self.goldFormat

        self.failedIndicies = kwargs['failedIndicies']\
            if ('failedIndicies' in kwargs) else set()
        self.kwargs['failedIndicies'] = self.failedIndicies

        self.length = self._fileLen(goldFilePath)

        self.indexOfFileReader = 0

    def __len__(self):
        return self.length

    def _fileLen(self, fname):
        i = -1
        with open(fname) as f:
            for i, l in enumerate(f):
                pass
            f.seek(0)
        return i + 1

    def _inferFormat(self):
        try:
            goldFile = self.goldFile
            line = goldFile.readline()
            goldFile.seek(0)
            line = line.strip()

            firstChar = line[0]
            if firstChar == '<':
                return 'XML'
            elif firstChar == '{':
                return 'JSON'

            return 'text'
        except Exception as err:
            raise Exception('Unable to Infer Gold File Format', err)

    def copy(self):
        '''
            returns a copy of the SummaryReaderObject
        '''
        return SummaryReaderObject(
            self.summaryFilePath, self.goldFilePath, **self.kwargs
        )

    def readOne(self):
        if self.indexOfFileReader > self.length - 1:
            raise IndexError('All Lines Have Been Read.\
                Call Copy if you need to re-read this object.')

        references = self._readReferences()

        if self.indexOfFileReader in self.failedIndicies:
            # If the summary failed then skip to the next set
            # references always need to be read first as the file
            # reader needs to advance to the next reference
            self.indexOfFileReader += 1
            return self.readOne()  # Recurse until you can read a summary
            # that has not failed

        summary = self.summariesFile.readline()
        self.indexOfFileReader += 1
        return (summary, references)

    def _readReferences(self):
        if self.goldFormat == 'JSON':
            referencesJSONString = self.goldFile.readline()
            refrencesJSON = json.loads(referencesJSONString)
            references = refrencesJSON['references']
            return references
        elif self.goldFormat == 'XML':
            raise Exception("Unable to Handle XML at this Time.\
                Please Elect to Use JSON Format")
        elif self.goldFormat == 'text':
            reference = self.goldFile.readline()
            return [reference]

    def readAll(self):
        '''
            Reads all remaining lines. Will return an empty list if the
            reader object has reached the end of the gold file.
        '''
        allLines = []
        try:
            for i in range(self.numSummaries):
                allLines.append(self.readOne())
        except IndexError:
            pass

        self._closeFiles()
        return allLines

    def _closeFiles(self):
        self.summariesFile.close()
        self.goldFile.close()

    def __del__(self):
        self._closeFiles()
