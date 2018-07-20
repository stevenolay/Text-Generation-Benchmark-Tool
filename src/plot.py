import plotly as py
import plotly.graph_objs as go
py.offline.init_notebook_mode()
from plotly.tools import FigureFactory as ff
import pandas as pd

def plotTable(file):
    df = pd.read_csv(file)
    table = ff.create_table(df)
    py.offline.plot(table)

'''
plotTable('results.csv')
"https://raw.githubusercontent.com/plotly/datasets/master/school_earnings.csv"
'''