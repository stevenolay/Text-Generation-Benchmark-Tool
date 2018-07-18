import requests


class Recollect:
    def __init__(self, language='en'):
        self.language = language
        self.URL = 'http://balsrini-wx-1:1089/summarize'

    def summarize(self, text, numSentences):
        requestBody = self.createRequestBody(text, numSentences)
        r = requests.post(self.URL, data=requestBody)
        r.raise_for_status()

        recollectResponseBody = r.text
        return recollectResponseBody

    def createRequestBody(self, text, numSentences):

        return {
            "textSize": numSentences,
            "language": self.language,
            "content": text,
            "summarizationUnit": 'sentence'
        }
