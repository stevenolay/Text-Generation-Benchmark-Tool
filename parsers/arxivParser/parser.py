import codecs
import json
import os

def parse(testLocation):
    os.makedirs('Arxiv/samples')
    os.makedirs('Arxiv/gold')
    with codecs.open(testLocation, 'r','utf-8') as src:
        with codecs.open('Arxiv/samples/arxiv.txt', 'w') as samp:
            with codecs.open('Arxiv/gold/arxiv_gold.txt', 'w') as abst:
                line = src.readline()

                while line:
                    lineJSON = json.loads(line)

                    articleTextList = lineJSON['article_text']
                    formattedArticleText = formatArticle(articleTextList)
                    samp.write('{0}\n'.format(formattedArticleText))

                    abstractTextList = lineJSON['abstract_text']
                    formattedAbstract = formatAbstract(abstractTextList)
                    abst.write('{0}\n'.format(formattedAbstract))

                    line = src.readline()

                samp.seek(-1, os.SEEK_END)
                samp.truncate()

                abst.seek(-1, os.SEEK_END)
                abst.truncate()

def formatArticle(articleTextList):
    return '[BREAK]'.join(articleTextList)

def formatAbstract(abstractTextList):
    hypothesis = ''.join(abstractTextList)
    hypothesis = hypothesis.replace('<S>', '')
    hypothesis = hypothesis.replace('</S>', '')

    hypothesis = hypothesis.strip()

    return hypothesis


parse('/Users/layne/Downloads/arxiv-release/train.txt')
