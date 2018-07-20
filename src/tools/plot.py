import plotly as py
import plotly.graph_objs as go
import plotly.figure_factory
py.offline.init_notebook_mode()
from plotly.tools import FigureFactory as ff
import pandas as pd
import os

def plotTable(file):
    resultsFilePath, resultsFileName = os.path.split(file)

    df = pd.read_csv(file)
    table = plotly.figure_factory.create_table(df)

    plotFileName = '{0}.html'.format(resultsFileName)
    filename = os.path.join(resultsFilePath, plotFileName)
    py.offline.plot(table, filename=filename)

'''
plotTable('results.csv')
"https://raw.githubusercontent.com/plotly/datasets/master/school_earnings.csv"
'''