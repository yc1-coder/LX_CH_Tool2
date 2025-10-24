import pandas as pd
import dash
from dash import dcc,html,Dash,Input,Output
import plotly.graph_objects as go
from collections import Counter



class  SiteProcess:                                                       #前15列是固定数据，封装
    def __init__ (self,file_path):
        self.df = pd.read_csv(file_path)
        self.header = []
        self.serial_number = None                                   #提取df中的SerialNumber
        self.config = None                                               #提取df中的BUILD_MATRIX_CONFIG
    def process_site(self):
        self.header = {'serial_header':'SerialNumber','config_header':'BUILD_MATRIX_CONFIG'}    #列名本身就是表头
        self.serial_number = self.df.iloc[:,2]
        self.config = self.df.iloc[:,12]


class DataVisual:
    def __init__(self,process):
        self.df = process.df
        self.column_names = self.df.columns.tolist()                                #直接提取列名，将列名转换为Python列表

    def load_data(self):
        y_data = self.df.iloc[5:,15:]                                                           #获取数据
        raw_columns = self.df.columns[15:]                                               #提取并格式化测试项列名
        self.test_columns = self.format_column_names(raw_columns)     #格式化后的列名作为X轴
        return y_data,self.test_columns                                                  #返回值

    def create_plot_data(self):                                                             #数据拼接（Sn,config,data）
        y_data, test_columns = self.load_data()
        serial_number = self.df.iloc[:, 2]
        config_data = self.df.iloc[:,12]
        create_dataframe = pd.concat([serial_number,config_data,y_data],axis=1)   #axis=1,沿着行方向拼接
        return create_dataframe

    def draw_chart(self):
        # 1. 数据准备
        plot_data = self.create_plot_data()
        x_axis_labels = self.test_columns

        # 2. 创建图表对象
        fig = go.Figure()

        # 3. 添加数据系列
        if len(plot_data) > 0 and len(x_axis_labels) > 0:
            # 获取Y数据列（从第3列开始，跳过SN和Config）
            y_columns = plot_data.columns[2:]

            # 确保数据维度匹配
            if len(x_axis_labels) == len(y_columns):
                # 统计每个config出现的次数
                config_counts = {}
                for index, row in plot_data.iterrows():
                    if not row[2:].isnull().any():
                        config = row[1]
                        if config not in config_counts:
                            config_counts[config] = 0
                        config_counts[config] += 1

                # 记录每个config是否已在图例中显示
                config_shown = {}

                # 为不同config分配颜色
                config_colors = {}
                color_palette = [
                    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
                ]
                color_index = 0

                # 为每一行数据创建一条线
                for index, row in plot_data.iterrows():
                    if not row[2:].isnull().any():
                        sn = row[0]
                        config = row[1]

                        # 为config分配颜色
                        if config not in config_colors:
                            config_colors[config] = color_palette[color_index % len(color_palette)]
                            color_index += 1

                        # 确定图例名称
                        if config_counts[config] > 1:
                            legend_name = f"{config}({config_counts[config]})"
                        else:
                            legend_name = config

                        # 确定是否在图例中显示
                        show_in_legend = False
                        if config not in config_shown:
                            config_shown[config] = True
                            show_in_legend = True

                        fig.add_trace(go.Scatter(
                            x=x_axis_labels,  # X轴数据
                            y=row[2:].values,  # Y轴数据
                            mode='lines+markers',  # 显示线条和标记
                            name=legend_name,  # 图例名称
                            legendgroup=config,  # 将相同config归为一组
                            showlegend=show_in_legend,  # 控制是否在图例中显示
                            line=dict(width=2, color=config_colors[config]),  # 显式设置颜色
                            marker=dict(size=6, color=config_colors[config])  # 显式设置颜色
                        ))

        # 4. 设置图表布局
        fig.update_layout(
            title=dict(text="EIRP-NB", x=0.5, xanchor='center'),
            xaxis_title="Channel",
            yaxis_title="测试值",
            template="plotly_white"
        )

        return fig

    def format_column_names(self, columns):    #格式化数据表头，提取画图的坐标信息
        """格式化列名，提取关键信息"""
        formatted = []
        for col in columns:
            if pd.isna(col):
                formatted.append("Unknown")
            elif ':' in str(col):
                # 从复杂字符串中提取有用信息
                parts = str(col).split(':')
                # 提取channel值等关键信息
                if 'channel=' in str(col):
                    # 提取channel的具体数值
                    channel_part = [p for p in parts if 'channel=' in p][0]
                    channel_value = channel_part.split('=')[1]
                    formatted.append(f"Channel {channel_value}")
                else:
                    formatted.append(parts[-2])  # 提取最后一个部分
            else:
                formatted.append(str(col))

        return formatted



def create_dash_app():
    processor = SiteProcess("extracted_data/EIRP-NB.csv")
    processor.process_site()

    visual = DataVisual(processor)

    app = Dash(__name__)
    fig = visual.draw_chart()
    app.layout = html.Div([
        html.H1("CH_Tool_Setting",style={"text-align": "center"}),
        dcc.Graph(figure=fig),
    ])
    return app


if __name__ == '__main__':

    app = create_dash_app()
    app.run(debug=True,port=8050)