import pandas as pd
import dash
from dash import dcc,html,Dash,Input,Output
import plotly.graph_objects as go
from collections import Counter

class  SiteProcess:                                                       #前15列是固定数据，封装
    def __init__ (self,file_path):
        self.df = pd.read_csv(file_path,index_col=False,skiprows=0)                                                           #存储传入的数据框架
        self.serial_number = None                                   #提取df中的SerialNumber
        self.config = None                                               #提取df中的BUILD_MATRIX_CONFIG
        self.header = []
    def process_site(self):
        self.header = {'serial_header':'SerialNumber','config_header':'BUILD_MATRIX_CONFIG'}  #列名本身就是表头
        self.serial_number = self.df['SerialNumber']
        self.config = self.df['BUILD_MATRIX_CONFIG']

class DataVisual:
    def __init__(self,process):
        self.df = process.df
    def load_data(self):
        y_data = self.df.iloc[6:,15:]
        print(y_data)




if __name__ == '__main__':
    processor = SiteProcess("extracted_data/EIRP-NB.csv")
    processor.process_site()
    visual = DataVisual(processor)
    visual.load_data()