'''
import plotly as py
py.offline.init_notebook_mode()
'''

import plotly.figure_factory
import plotly.offline
import plotly.graph_objs as go


import pandas as pd
import os

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