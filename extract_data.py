import pandas as pd
#读取xlsx配置文件
columns_config =  pd.read_excel('Setting.xlsx',
                                                        sheet_name='Sheet1',
                                                        skiprows=23,
                                                        nrows=16,               #读取17行
                                                        usecols='A:D' )      #读取A到D列
# 获取第一列所有非空值
column_names = columns_config.columns.tolist()
column_first = column_names[0]  # 获取第一列的列名
print(column_first)
column_second = column_names[1]
print(column_second)
column_third = columns_config.iloc[:,2]
print(column_third)
column_fourth = column_names[3]
print(column_fourth)
print(columns_config)


# df = pd.read_csv('Jade_EVT_Omnia_Combined_Auto-0704.csv')
# print(df)