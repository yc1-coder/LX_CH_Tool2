from abc import ABC,abstractmethod
import pandas as pd
import re
import math
import dash
from dash import dcc,html,Dash,Input,Output
import plotly.graph_objects as go
from collections import Counter

class BaseFrequencyChart(ABC):
    '''基础频率图表类 - 定义通用接口'''
    def __init__(self,df,chart_title):
        self.df = df                                      #存储传入的数据框
        self.chart_title = chart_title          #存储图表标题
        self.frequencies = []                        #存储频率列名的列表
        self.frequency_labels = []                #存储频率标签的列表
        self.traces = []                                 #存储表轨迹的列表
        self.layout = None                            #存储图表布局对象
        self._process_data()                        #初始化处理
        self._process_columns()
        self._calculate_ranges()
    def _process_data(self):
        '''数据预处理 - 直接处理原CSV'''
        new_columns = []
        # 前15列保持原名
        info_columns = min(15, len(self.df.columns))
        new_columns.extend(self.df.columns[:info_columns])
        # 处理频率列名
        for col in self.df.columns[info_columns:]:
            freq_match = re.search(r'freq=([0-9.]+)GHz', col)
            if freq_match:
                new_columns.append(f'{freq_match.group(1)}GHz')
            else:
                new_columns.append(col)

        self.df.columns = new_columns
    def _process_columns(self):
        '''处理列名 - 子类可以重写'''
        self._extract_frequency_columns()      #提取列名
        self._generate_frequency_chart()        #生成标签
    def _extract_frequency_columns(self):
        '''提取频率列 - 智能识别包含GHz的列'''
        start_index = getattr(self,'start_index',16)
        #只选择包含GHz的列作为频率列
        self.frequencies = [col for col in self.df.columns[start_index:] if 'GHz' in col]
    def _generate_frequency_chart(self):
        '''生成频率标签'''
        self.frequency_labels = []
        for col in self.frequencies:
            #更准确的提取频率数值
            freq_match = re.search(r'(\d+\.?\d*)GHz',col)
            if freq_match:
                freq_val = float(freq_match.group(1))
                self.frequency_labels.append(f"{freq_val:.2f}")
            else:
                #备用方案
                freq_str = col.replace('GHz', '').strip()
                try:
                    freq_val = float(freq_str)
                    self.frequency_labels.append(f"{freq_val:.2f}")
                except ValueError:
                    self.frequency_labels.append(freq_str)       #如果转换失败（字符串不是有效数字），直接使用原始字符串
    def _calculate_ranges(self):
        '''计算数据范围'''
        self._calculate_y_axis_range()                            #计算Y轴的范围
        self._calculate_intervals()                                   #计算间隔
    def _calculate_y_axis_range(self):
        '''计算Y轴范围'''
        all_y_values = []
        for col in self.frequencies:
            valid_values = self.df[col].dropna().tolist()   #从数据框中获取当前列的数据，移除空值数据点，再转为列表
            all_y_values.extend(valid_values)                 #extend 方法将列表中的每个元素逐一添加
        if not all_y_values:
            self.y_min,self.y_max = 0,1
        else:
            self.y_min = min(all_y_values)
            self.y_max = max(all_y_values)

        margin = getattr(self,'margin',2)
        self.y_axis_min = math.floor(self.y_min) - margin     #向下取整最小值
        self.y_axis_max = math.ceil(self.y_max) + margin     #向上取整最大值
    def _calculate_intervals(self):
        '''计算间隔'''
        y_range = self.y_axis_max -self.y_axis_min
        if y_range <= 5:                  #如果Y轴范围小于等于5个单位
            self.interval = 0.5           #设置间隔为0.5个单位
        elif y_range <= 10:
            self.interval =1
        else:
            self.interval =math.ceil(y_range / 10)   #如果Y轴范围大于10个单位，则设置间隔为Y轴范围除以10的整数部分
    @abstractmethod
    def create_traces(self):
        '''创建图表轨迹 - 必须由子类实现'''
        pass
    def create_layout(self):
        '''创建图表布局'''
        self.layout = go.Layout(
            #图表的基本设置
            title = self.chart_title,
            #X轴设置
            xaxis = dict(
                title = "频率(GHz)",                           #X轴设置
                tickmode='array',                             #刻度模式为数组形式
                tickvals = self.frequency_labels,       #刻度位置
                ticktext = self.frequency_labels      #刻度显示文本
            ),
            #Y轴设置
            yaxis=dict(
                title = "测量值(dBm)",
                range=[self.y_axis_min,self.y_axis_max],   #Y轴范围
                dtick = self.interval,
                showgrid = True,                                          #显示网格线
                gridwidth = 1,                                               #网格线宽度
                gridcolor = 'lightgray'                                  #网格线颜色
            ),
            #图例设置
            legend = dict(y=0.98,
                          x=1.2,
                          xanchor = 'right',
                          yanchor = 'top',
                          bgcolor = 'rgba(255,255,255,0.5)',
                          groupclick = "toggleitem",
                          font=dict(size=10)
        ),
            #图表尺寸和边距
            width = 1000,
            height=400,
            margin = dict(t=50,b=80,l=50,r=50)
        )
    def generate_chart(self):
        '''生成完整图表'''
        self.create_traces()
        self.create_layout()
        return go.Figure(data=self.traces,layout=self.layout)
class BasicFrequencyChart(BaseFrequencyChart):
    '''基础(不带上下限)频率图表'''
    def create_traces(self):
        '''创建基础轨迹'''
        self.traces = []
        added_to_legend = set()
        #统计序列号出现次数
        config_numbers = [str(self.df.iloc[i,12]) for i in range(3,len(self.df))]    #len(self.df):数据行
        serial_total_count = Counter(config_numbers)
        # 在循环外部定义颜色映射
        config_color_mapping = {}
        available_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan',
                                'magenta', 'yellow', 'black', 'lime', 'teal', 'navy', 'maroon', 'olive', 'indigo','turquoise']
        color_index = 0

        # 先预分配所有唯一CONFIG的颜色
        for config_val in set(config_numbers):
            if config_val not in config_color_mapping:
                config_color_mapping[config_val] = available_colors[color_index % len(available_colors)]
                color_index += 1

        #为每一行数据创建轨迹
        for i in range(len(self.df)):
            config_value = str(self.df.iloc[i,12])
            total_count = serial_total_count[config_value]
            if total_count > 1:
                display_config = f"{config_value}({total_count})"
            else:
                display_config = config_value
            config_value = str(self.df.iloc[i,12])        #根据实际索引列调整
            # 使用颜色映射
            color = config_color_mapping[config_value]
            #获取该设备在各频率下的数据
            y_data = self.df.iloc[i][self.frequencies].tolist()
            #用于跟踪已经添加到图例中的设备名称
            display_names = {'SN':2, 'CONFIG':12}
            #构建hover(数据点悬停)信息
            hover_info = ""
            for col_name,color_index in display_names.items():
                col_value = str(self.df.iloc[i,color_index]) if pd.notna(self.df.iloc[i,color_index]) else ""
                hover_info += f"<b>{col_name}:</b> {col_value}<br>"
            #移除末尾多余的<br>标签
            hover_info = hover_info.rstrip('<br>')
            #为每个频率点添加详情信息
            hover_template = '<br>'.join([f'{hover_info}', '<b>Band:</b>%{x:.2f}', '<b>Value:</b> %{y}'])
            #确定是否在图例中显示该项
            show_in_legend =  False
            if display_config not in added_to_legend:
                show_in_legend = True
                added_to_legend.add(display_config)
            trace = go.Scatter(
                x = self.frequency_labels,
                y = y_data,
                mode = 'lines+markers',
                name = display_config,
                legendgroup = config_value,
                showlegend = show_in_legend,
                line = dict(shape='linear',color=color),
                marker = dict(size=3,color=color),
                hovertemplate = hover_template)
            self.traces.append(trace)
class FrequencyChartWithLimits(BaseFrequencyChart):
    '''带上下限的频率图表'''
    def __init__(self,df,chart_title,upper_limit_row=1,lower_limit_row=2):
        self.upper_limit_row = upper_limit_row
        self.lower_limit_row = lower_limit_row
        super().__init__(df,chart_title)
    def create_traces(self):
        '''创建带上下限的轨迹'''
        self.traces = []
        added_to_legend = set()
        #统计序config出现次数
        config_numbers = [str(self.df.iloc[i,12]) for i in range(3,len(self.df))]
        serial_total_count = Counter(config_numbers)
        #在循环外部定义颜色映射
        config_color_mapping = {}
        available_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan','magenta','yellow','black','lime','teal','navy','maroon','olive','indigo','turquoise']
        color_index = 0
        #先预分配所有唯一CONFIG的颜色
        for config_val in set(config_numbers):
            if config_val not in config_color_mapping:
                config_color_mapping[config_val] = available_colors[color_index % len(available_colors)]
                color_index += 1
        #为每一行创建数据轨迹
        for i in range(len(self.df)):
            config_value = str(self.df.iloc[i,12])
            total_count = serial_total_count[config_value]
            if total_count > 1:
                display_config = f"{config_value}({total_count})"
            else:
                display_config = config_value
            config_value = str(self.df.iloc[i,12])      #根据实际索引列调整
            #使用颜色映射
            color = config_color_mapping[config_value]
            #获取该设备在各频率下的数据
            y_data = self.df.iloc[i][self.frequencies].tolist()
            #用于跟踪已经添加到图例中的设备名称
            display_names = {'SN':2,'CONFIG':12}
            #构建hover(数据点悬停)信息
            hover_info = ""
            for col_name,color_index in display_names.items():
                col_value = str(self.df.iloc[i,color_index]) if pd.notna(self.df.iloc[i,color_index]) else ""
                hover_info += f"<b>{col_name}:</b>{col_value}</br>"
            #移除末尾多余的<br>标签
            hover_info = hover_info.rstrip('<br>')
            #为每个频率点添加详情信息
            hover_template = '<br>'.join([f'{hover_info}','<b>Band:</b>%{x:.2f}','<b>Value:</b>%{y}'])
            #确定是否在图例中显示该项
            show_in_legend = False
            if display_config not in added_to_legend:
                show_in_legend =True
                added_to_legend.add(display_config)

            trace = go.Scatter(
                x=self.frequency_labels,
                y=y_data,
                mode='lines+markers',
                name=display_config,
                legendgroup=config_value,
                showlegend=show_in_legend,
                line=dict(shape='linear',color=color),
                marker=dict(size=3,color=color),
                hovertemplate=hover_template
            )
            self.traces.append(trace)
        # 添加上下限线
        self._add_limit_lines()

    def _add_limit_lines(self):
        '''添加上下限线'''
        # 确保有足够的列来获取限制值
        if len(self.frequencies) > 0:
            # 检查并添加上限线
            upper_limit_value = float(self.df.iloc[self.upper_limit_row][self.frequencies[0]])
            upper_trace = go.Scatter(
                x=self.frequency_labels,
                y=[upper_limit_value] * len(self.frequency_labels),
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='上限(Upper Limit)',
                showlegend=True,
                hovertemplate=f'<b>上限:</b> {upper_limit_value}dBm<extra></extra>'
            )
            # 下限线
            lower_limit_value = float(self.df.iloc[self.lower_limit_row][self.frequencies[0]])
            lower_trace = go.Scatter(
                x=self.frequency_labels,
                y=[lower_limit_value] * len(self.frequency_labels),
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='下限(Lower Limit)',
                showlegend=True,
                hovertemplate=f'<b>下限:</b> {lower_limit_value}dBm<extra></extra>'
            )

            self.traces.extend([upper_trace, lower_trace])

    #使用方式清晰
if __name__ == '__main__':
    # 读取原始数据
    df = pd.read_csv('Jade_EVT_Omnia_Combined_Auto-0704.csv',header=1)

    df_1 = df.iloc[:,0:23].drop(df.columns[15],axis=1)
    #直接跳过第四行（PDCA）
    df_1 = df_1.drop(index=1).reset_index(drop=True)

    cols_needed_2  = list(range(0,15)) + list(range(30,37))
    df_2 = df.iloc[:,cols_needed_2]
    df_2 = df_2.drop(index=1).reset_index(drop=True)

    cols_needed_3 = list(range(0,15)) + list(range(45,52))
    df_3 = df.iloc[:,cols_needed_3]
    df_3 = df_3.drop(index=1).reset_index(drop=True)

    cols_needed_4 = list(range(0,15)) + list(range(52,59))
    df_4 = df.iloc[:,cols_needed_4]
    df_4 = df_4.drop(index=1).reset_index(drop=True)

    cols_needed_5 = list(range(0,15)) + list(range(59,66))
    df_5 = df.iloc[:,cols_needed_5]
    df_5 = df_5.drop(index=1).reset_index(drop=True)

    cols_needed_6 = list(range(0,15)) + list(range(66,73))
    df_6 = df.iloc[:,cols_needed_6]
    df_6 = df_6.drop(index=1).reset_index(drop=True)

    cols_needed_7 = list(range(0,15)) + list(range(75,82))
    df_7 = df.iloc[:,cols_needed_7]
    df_7 = df_7.drop(index=1).reset_index(drop=True)

    cols_needed_8 = list(range(0,15)) + list(range(82,89))
    df_8 = df.iloc[:,cols_needed_8]
    df_8 = df_8.drop(index=1).reset_index(drop=True)

    cols_needed_9 = list(range(0,15)) + list(range(90,97))
    df_9 = df.iloc[:,cols_needed_9]
    df_9 = df_9.drop(index=1).reset_index(drop=True)

    # cols_needed_10 = list(range(0,15)) + list(range(104,111))
    # df_10= df.iloc[:,cols_needed_10]
    # df_10 = df_10.drop(index=1).reset_index(drop=True)

    # 创建不同类型的图表
    basic_chart1 = BasicFrequencyChart(df_1, "基础频率响应图")
    basic_chart2 = BasicFrequencyChart(df_2, "基础频率响应图")
    basic_chart3 = FrequencyChartWithLimits(df_3, "带上下限的频率响应图")
    basic_chart4 = BasicFrequencyChart(df_4,"基础频率响应图")
    basic_chart5 = BasicFrequencyChart(df_5,"基础频率响应图")
    basic_chart6 = BasicFrequencyChart(df_6,"基础频率响应图")
    basic_chart7 = BasicFrequencyChart(df_7,"基础频率响应图")
    basic_chart8 = BasicFrequencyChart(df_8,"基础频率响应图")
    basic_chart9 = BasicFrequencyChart(df_9,"基础频率响应图")
    # basic_chart10 = FrequencyChartWithLimits(df_10,"带上下限的频率响应图")
    # 对于带限制的图表，需要确保数据中有相应的限制行
    # 生成图表
    fig1 = basic_chart1.generate_chart()
    fig2 = basic_chart2.generate_chart()
    fig3 = basic_chart3.generate_chart()
    fig4= basic_chart4.generate_chart()
    fig5 = basic_chart5.generate_chart()
    fig6 = basic_chart6.generate_chart()
    fig7 = basic_chart7.generate_chart()
    fig8 = basic_chart8.generate_chart()
    fig9 = basic_chart9.generate_chart()

    # 创建Dash应用，将所有图表整合到一个网页中
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("频率响应图表集合", style={'text-align': 'center'}),

        # 将所有图表垂直排列
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig4),
        dcc.Graph(figure=fig5),
        dcc.Graph(figure=fig6),
        dcc.Graph(figure=fig7),
        dcc.Graph(figure=fig8),
        dcc.Graph(figure=fig9)
    ])

    # 运行应用
    app.run(debug=True, port=8050)