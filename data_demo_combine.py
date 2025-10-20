from abc import ABC, abstractmethod
import pandas as pd
import re
import math
import dash
from dash import dcc, html, Dash, Input, Output
import plotly.graph_objects as go
from collections import Counter

class BaseFrequencyChart(ABC):
    '''基础频率图表类 - 定义通用接口'''
    def __init__(self, df, chart_title):
        self.df = df  # 存储传入的数据框
        self.chart_title = chart_title  # 存储图表标题
        self.frequencies = []  # 存储频率列名的列表
        self.frequency_labels = []  # 存储频率标签的列表
        self.traces = []  # 存储表轨迹的列表
        self.layout = None  # 存储图表布局对象
        self._process_data()  # 初始化处理
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
        self._extract_frequency_columns()  # 提取列名
        self._generate_frequency_chart()  # 生成标签

    def _extract_frequency_columns(self):
        '''提取频率列 - 智能识别包含GHz的列'''
        start_index = getattr(self, 'start_index', 16)
        # 只选择包含GHz的列作为频率列
        self.frequencies = [col for col in self.df.columns[start_index:] if 'GHz' in col]

    def _generate_frequency_chart(self):
        '''生成频率标签'''
        self.frequency_labels = []
        for col in self.frequencies:
            # 更准确的提取频率数值
            freq_match = re.search(r'(\d+\.?\d*)GHz', col)
            if freq_match:
                freq_val = float(freq_match.group(1))
                self.frequency_labels.append(f"{freq_val:.2f}")
            else:
                # 备用方案
                freq_str = col.replace('GHz', '').strip()
                try:
                    freq_val = float(freq_str)
                    self.frequency_labels.append(f"{freq_val:.2f}")
                except ValueError:
                    self.frequency_labels.append(freq_str)  # 如果转换失败（字符串不是有效数字），直接使用原始字符串

    def _calculate_ranges(self):
        '''计算数据范围'''
        self._calculate_y_axis_range()  # 计算Y轴的范围
        self._calculate_intervals()  # 计算间隔

    def _calculate_y_axis_range(self):
        '''计算Y轴范围'''
        all_y_values = []
        for col in self.frequencies:
            valid_values = self.df[col].dropna().tolist()  # 从数据框中获取当前列的数据，移除空值数据点，再转为列表
            all_y_values.extend(valid_values)  # extend 方法将列表中的每个元素逐一添加
        if not all_y_values:
            self.y_min, self.y_max = 0, 1
        else:
            self.y_min = min(all_y_values)
            self.y_max = max(all_y_values)

        margin = getattr(self, 'margin', 2)
        self.y_axis_min = math.floor(self.y_min) - margin  # 向下取整最小值
        self.y_axis_max = math.ceil(self.y_max) + margin  # 向上取整最大值

    def _calculate_intervals(self):
        '''计算间隔'''
        y_range = self.y_axis_max - self.y_axis_min
        if y_range <= 5:  # 如果Y轴范围小于等于5个单位
            self.interval = 0.5  # 设置间隔为0.5个单位
        elif y_range <= 10:
            self.interval = 1
        else:
            self.interval = math.ceil(y_range / 10)  # 如果Y轴范围大于10个单位，则设置间隔为Y轴范围除以10的整数部分

    @abstractmethod
    def create_traces(self):
        '''创建图表轨迹 - 必须由子类实现'''
        pass

    def create_layout(self):
        '''创建图表布局'''
        self.layout = go.Layout(
            # 图表的基本设置
            title=self.chart_title,
            # X轴设置
            xaxis=dict(
                title="频率(GHz)",  # X轴设置
                tickmode='array',  # 刻度模式为数组形式
                tickvals=self.frequency_labels,  # 刻度位置
                ticktext=self.frequency_labels  # 刻度显示文本
            ),
            # Y轴设置
            yaxis=dict(
                title="测量值(dBm)",
                range=[self.y_axis_min, self.y_axis_max],  # Y轴范围
                dtick=self.interval,
                showgrid=True,  # 显示网格线
                gridwidth=1,  # 网格线宽度
                gridcolor='lightgray'  # 网格线颜色
            ),
            # 图例设置
            legend=dict(y=0.98,
                        x=1.2,
                        xanchor='right',
                        yanchor='top',
                        bgcolor='rgba(255,255,255,0.5)',
                        groupclick="toggleitem",
                        font=dict(size=10)
                        ),
            # 图表尺寸和边距
            width=1000,
            height=400,
            margin=dict(t=50, b=80, l=50, r=50)
        )

    def generate_chart(self):
        '''生成完整图表'''
        self.create_traces()
        self.create_layout()
        return go.Figure(data=self.traces, layout=self.layout)


class BasicFrequencyChart(BaseFrequencyChart):
    '''基础(不带上下限)频率图表'''

    def create_traces(self):
        '''创建基础轨迹'''
        self.traces = []
        added_to_legend = set()
        # 统计序列号出现次数
        config_numbers = [str(self.df.iloc[i, 12]) for i in range(len(self.df))]
        serial_total_count = Counter(config_numbers)
        # 在循环外部定义颜色映射
        config_color_mapping = {}
        available_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan',
                            'magenta', 'yellow', 'black', 'lime', 'teal', 'navy', 'maroon', 'olive', 'indigo',
                            'turquoise']
        color_index = 0

        # 先预分配所有唯一CONFIG的颜色
        for config_val in set(config_numbers):
            if config_val not in config_color_mapping:
                config_color_mapping[config_val] = available_colors[color_index % len(available_colors)]
                color_index += 1

        # 为每一行数据创建轨迹
        for i in range(len(self.df)):
            config_value = str(self.df.iloc[i, 12])
            total_count = serial_total_count[config_value]
            if total_count > 1:
                display_config = f"{config_value}({total_count})"
            else:
                display_config = config_value
            config_value = str(self.df.iloc[i, 12])  # 根据实际索引列调整
            # 使用颜色映射
            color = config_color_mapping[config_value]
            # 获取该设备在各频率下的数据
            y_data = self.df.iloc[i][self.frequencies].tolist()
            # 用于跟踪已经添加到图例中的设备名称
            display_names = {'SN': 2, 'CONFIG': 12}
            # 构建hover(数据点悬停)信息
            hover_info = ""
            for col_name, color_index in display_names.items():
                col_value = str(self.df.iloc[i, color_index]) if pd.notna(self.df.iloc[i, color_index]) else ""
                hover_info += f"<b>{col_name}:</b> {col_value}<br>"
            # 移除末尾多余的<br>标签
            hover_info = hover_info.rstrip('<br>')
            # 为每个频率点添加详情信息
            hover_template = '<br>'.join([f'{hover_info}', '<b>Band:</b>%{x:.2f}', '<b>Value:</b> %{y}'])
            # 确定是否在图例中显示该项
            show_in_legend = False
            if display_config not in added_to_legend:
                show_in_legend = True
                added_to_legend.add(display_config)
            trace = go.Scatter(
                x=self.frequency_labels,
                y=y_data,
                mode='lines+markers',
                name=display_config,
                legendgroup=config_value,
                showlegend=show_in_legend,
                line=dict(shape='linear', color=color),
                marker=dict(size=3, color=color),
                hovertemplate=hover_template
            )
            self.traces.append(trace)


class FrequencyChartWithLimits(BaseFrequencyChart):
    '''带上下限的频率图表'''

    def __init__(self, df, chart_title, upper_limit_row=1, lower_limit_row=2):
        self.upper_limit_row = upper_limit_row
        self.lower_limit_row = lower_limit_row
        super().__init__(df, chart_title)

    def create_traces(self):
        '''创建带上下限的轨迹'''
        self.traces = []
        # 创建主数据轨迹
        serial_numbers = [str(self.df.iloc[i, 12]) for i in range(len(self.df))]
        serial_total_count = Counter(serial_numbers)
        added_to_legend = set()
        column_names = ['SN', 'CONFIG', 'PRODUCT', 'ID']

        # 在循环外部定义颜色映射
        config_color_mapping = {}
        available_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan',
                            'magenta', 'yellow', 'black', 'lime', 'teal', 'navy', 'maroon', 'olive', 'indigo',
                            'turquoise']
        color_index = 0

        # 先预分配所有唯一CONFIG的颜色（排除限制行）
        for i in range(3, len(self.df)):
            if i == self.upper_limit_row or i == self.lower_limit_row:
                continue
            config_value = str(self.df.iloc[i, 12])
            if config_value not in config_color_mapping:
                config_color_mapping[config_value] = available_colors[color_index % len(available_colors)]
                color_index += 1

        # 跳过标题行和限制行，从第4行开始处理数据 (索引3)
        for i in range(3, len(self.df)):
            # 跳过限制行
            if i == self.upper_limit_row or i == self.lower_limit_row:
                continue

            serial_number = str(self.df.iloc[i, 12])
            total_count = serial_total_count[serial_number]
            display_serial_number = f"{serial_number}({total_count})" if total_count > 1 else serial_number

            config_value = str(self.df.iloc[i, 12])
            color = config_color_mapping[config_value]

            y_data = self.df.iloc[i][self.frequencies].tolist()

            hover_info = ""
            for j in range(min(4, len(column_names))):  # 确保不超出列数
                col_value = str(self.df.iloc[i, j]) if pd.notna(self.df.iloc[i, j]) else ""
                hover_info += f"<b>{column_names[j]}:</b> {col_value}<br>"

            hover_template = '<br>'.join([f'{hover_info}', '<b>频率:</b> %{x}GHz', '<b>测量值:</b> %{y} dBm'])

            show_in_legend = display_serial_number not in added_to_legend
            if show_in_legend:
                added_to_legend.add(display_serial_number)

            trace = go.Scatter(
                x=self.frequency_labels,
                y=y_data,
                mode='lines+markers',
                name=display_serial_number,
                legendgroup=serial_number,
                showlegend=show_in_legend,
                line=dict(shape='linear', color=color),
                marker=dict(size=3, color=color),
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


def save_complete_dashboard(figs, titles, filename):
    """
    保存包含完整布局的HTML文件
    """
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Jade-EVT-Omnia-Combined-Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }
        .container {
            display: flex;
            flex-direction: row;
        }
        .control-panel {
            width: 200px;
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-right: 20px;
        }
        .charts-container {
            flex: 1;
        }
        .chart {
            margin-bottom: 30px;
            background-color: white;
            border-radius: 5px;
            padding: 15px;
        }
        .control-panel h3 {
            text-align: center;
            margin-top: 0;
        }
        select {
            width: 190px;
            height: 30px;
            margin-bottom: 30px;
            padding: 5px;
            font-size: 14px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        /* 添加平滑滚动效果 */
        html {
            scroll-behavior: smooth;
        }
    </style>
</head>
<body>
    <h1 class="header">Jade-EVT-Omnia-Combined-Demo</h1>
    <div class="container">
        <div class="control-panel">
            <h3>Display Chart - All</h3>
            <select id="chartSelector" onchange="navigateToChart()">
"""

    # 添加选项
    for i in range(len(figs)):
        html_content += f'<option value="chart-{i + 1}-container">Display Chart - {i + 1}</option>\n'

    html_content += """            </select>
            <div style="margin-top: 20px;">
                <label>可以添加更多组件</label>
            </div>
        </div>
        <div class="charts-container">
"""

    # 添加图表
    for i, (fig, title) in enumerate(zip(figs, titles)):
        html_content += f'            <div class="chart" id="chart-{i + 1}-container"><h2>{title}</h2>{fig.to_html(include_plotlyjs="cdn")}</div>\n'

    # 添加JavaScript实现跳转功能
    html_content += """        </div>
    </div>
    <script>
        function navigateToChart() {
            var selector = document.getElementById("chartSelector");
            var selectedValue = selector.value;

            // 使用scrollIntoView实现平滑滚动
            var element = document.getElementById(selectedValue);
            if (element) {
                element.scrollIntoView({behavior: 'smooth', block: 'start'});
            }
        }

        // 页面加载完成后绑定事件
        document.addEventListener('DOMContentLoaded', function() {
            var selector = document.getElementById("chartSelector");
            if (selector) {
                selector.addEventListener('change', navigateToChart);
            }
        });
    </script>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML文件已保存: {filename}")


if __name__ == '__main__':
    # 读取原始数据
    df = pd.read_csv('Jade_EVT_Omnia_Combined_Auto-0704.csv', header=1)

    df_1 = df.iloc[:, 0:22].drop(df.columns[15], axis=1)
    # 直接跳过第四行（PDCA）
    df_1 = df_1.drop(index=1).reset_index(drop=True)

    cols_needed_2 = list(range(0, 15)) + list(range(30, 37))
    df_2 = df.iloc[:, cols_needed_2]
    df_2 = df_2.drop(index=1).reset_index(drop=True)

    cols_needed_3 = list(range(0, 15)) + list(range(45, 52))
    df_3 = df.iloc[:, cols_needed_3]
    df_3 = df_3.drop(index=1).reset_index(drop=True)

    cols_needed_4 = list(range(0, 15)) + list(range(52, 59))
    df_4 = df.iloc[:, cols_needed_4]
    df_4 = df_4.drop(index=1).reset_index(drop=True)

    cols_needed_5 = list(range(0, 15)) + list(range(59, 66))
    df_5 = df.iloc[:, cols_needed_5]
    df_5 = df_5.drop(index=1).reset_index(drop=True)

    cols_needed_6 = list(range(0, 15)) + list(range(66, 73))
    df_6 = df.iloc[:, cols_needed_6]
    df_6 = df_6.drop(index=1).reset_index(drop=True)

    cols_needed_7 = list(range(0, 15)) + list(range(75, 82))
    df_7 = df.iloc[:, cols_needed_7]
    df_7 = df_7.drop(index=1).reset_index(drop=True)

    cols_needed_8 = list(range(0, 15)) + list(range(82, 89))
    df_8 = df.iloc[:, cols_needed_8]
    df_8 = df_8.drop(index=1).reset_index(drop=True)

    cols_needed_9 = list(range(0, 15)) + list(range(90, 97))
    df_9 = df.iloc[:, cols_needed_9]
    df_9 = df_9.drop(index=1).reset_index(drop=True)

    # 创建不同类型的图表
    basic_chart1 = BasicFrequencyChart(df_1, "基础频率响应图 - Chamber Offset")
    basic_chart2 = BasicFrequencyChart(df_2, "基础频率响应图 - Directivity ant=ant_0")
    basic_chart3 = FrequencyChartWithLimits(df_3, "带上下限的频率响应图 - Directivity Omnia=0")
    basic_chart4 = BasicFrequencyChart(df_4, "基础频率响应图 - EdgeAsymmetry")
    basic_chart5 = BasicFrequencyChart(df_5, "基础频率响应图 - EIRP ant=ant_0")
    basic_chart6 = BasicFrequencyChart(df_6, "基础频率响应图 - EIRP Omnia=0")
    basic_chart7 = BasicFrequencyChart(df_7, "基础频率响应图 - EIRP_Corrected Omnia=0")
    basic_chart8 = BasicFrequencyChart(df_8, "基础频率响应图 - EIRP_Secondary Omnia=0")
    basic_chart9 = BasicFrequencyChart(df_9, "基础频率响应图 - FF_TransformTime Omnia=0")

    # 生成图表
    fig1 = basic_chart1.generate_chart()
    fig2 = basic_chart2.generate_chart()
    fig3 = basic_chart3.generate_chart()
    fig4 = basic_chart4.generate_chart()
    fig5 = basic_chart5.generate_chart()
    fig6 = basic_chart6.generate_chart()
    fig7 = basic_chart7.generate_chart()
    fig8 = basic_chart8.generate_chart()
    fig9 = basic_chart9.generate_chart()

    # 保存为HTML文件
    figs = [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9]
    titles = [
        "The frequency response of Chamber Offset",
        "The frequency response of Directivity ant=ant_0",
        "The frequency response of Directivity Omnia=0 with limits",
        "The frequency response of EdgeAsymmetry",
        "The frequency response of EIRP ant=ant_0",
        "The frequency response of EIRP Omnia=0",
        "The frequency response of EIRP_Corrected Omnia=0",
        "The frequency response of EIRP_Secondary Omnia=0",
        "The frequency response of FF_TransformTime Omnia=0"
    ]
    save_complete_dashboard(figs, titles, "Jade_EVT_Omnia_Combined_Auto-0704.html")

    # 创建Dash应用
    app = dash.Dash(__name__, title="Jade-EVT-Omnia-Combined-Demo")

    # 定义应用布局
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.H1("Jade-EVT-Omnia-Combined-Demo",
                style={'text-align': 'center', 'font-family': 'Arial, sans-serif', 'margin-bottom': '30px',
                       'color': '#333'}),
        # 主要内容区域 - 使用flex布局实现左右结构
        html.Div([
            # 左侧控制面板区域
            html.Div([html.H3("Display Chart - ALL", style={'text-align': 'center', 'margin-top': '0'}),
                      # 下拉菜单
                      dcc.Dropdown(id='control-panel-dropdown',
                                   options=[{'label': f'Display Chart - {i + 1}', 'value': f'chart-{i + 1}'}
                                            for i in range(len(figs))],
                                   value='chart-1',  # 默认选中项
                                   style={'width': '190px', 'margin-bottom': '30px'},
                                   clearable=False, searchable=False),
                      # 可以添加更多控件
                      html.Div([
                          html.Label("可以添加更多组件"),
                          # 可以添加其他控制元素
                      ], style={'margin-top': '20px'})
                      ], style={'width': '200px', 'background-color': '#e9ecef', 'padding': '15px',
                                'border-radius': '5px', 'margin-right': '20px'}),
            # 右侧图表区域
            html.Div([
                # 动态生成图表容器
                html.Div([
                    html.Div([
                        html.H2(titles[i], id=f'chart-{i + 1}-title'),
                        dcc.Graph(id=f'chart-{i + 1}', figure=fig,
                                  style={'margin-bottom': '30px' if i < len(figs) - 1 else '0px'})
                    ], id=f'chart-{i + 1}-container')
                    for i, (fig, title) in enumerate(zip(figs, titles))
                ])
            ], style={'flex': 1})  # 左右并排布局
        ], style={'display': 'flex', 'flex-direction': 'row'}),
    ], style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px', 'background-color': '#f9f9f9'})

    app.clientside_callback(
        """
        function(value) {
            setTimeout(function() {
                var element = document.getElementById(value + '-container');
                if (element) {
                    element.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }, 100);
            return value;
        }
        """,
        Output('control-panel-dropdown', 'data'),  # 一个虚拟的输出
        Input('control-panel-dropdown', 'value')
    )

    # 运行应用
    app.run(debug=True, port=8050)
