import pandas as pd
import re
import os

# 读取配置和数据文件
columns_config = pd.read_excel('Setting.xlsx',
                               sheet_name='Sheet1',
                               skiprows=22,
                               nrows=17,
                               usecols='A:D')
columns_config.columns = range(len(columns_config.columns))
# 获取需要列表（第四列的正则表达式）
table_header_3 = columns_config.iloc[:, 3].dropna().tolist()
# 获取第三列的文件名标识
table_header_2 = columns_config.iloc[:, 2].dropna().tolist()
print(table_header_2)
# 读取CSV,获取完整数据，包括所有列
df = pd.read_csv('Jade_EVT_Omnia_Combined_Auto-0704.csv', skiprows=1)
#获取前15列数据
first_15_columns = df.iloc[:, :15]
# 创建输出文件夹
output_folder = "extracted_data"
os.makedirs(output_folder, exist_ok=True)
# 按正则表达式分类数据
classified_data = {}
# 创建正则表达式与文件名的映射
rule_to_filename = {}
# 建立规则与文件名的对应关系
for i, rule in enumerate(table_header_3):
    if i < len(table_header_2):
        rule_to_filename[rule] = str(table_header_2[i])

for rule in table_header_3:
    # 为每个正则表达式创建一个匹配的列列表
    matched_columns = []
    for col in df.columns:
        try:
            if re.search(rule, col):
                matched_columns.append(col)
        except re.error as e:
            print(f"正则表达式错误 {rule}: {e}")
    # 如果有匹配的列，则提取这些列的数据
    if matched_columns:
        classified_data[rule] = df[matched_columns]
        # print(f"正则表达式 '{rule}' 匹配的列: {matched_columns}")
# 按照原始规则列表顺序保存数据
for i, rule in enumerate(table_header_3):
    if rule in classified_data:
        # 使用第三列的内容作为文件名
        if i < len(table_header_2):
            filename_base = str(table_header_2[i])
        else:
            filename_base = "result"
        combined_data = pd.concat([first_15_columns,classified_data[rule]],axis=1)
        # 构造完整路径
        filename = os.path.join(output_folder, f"{filename_base}.csv")
        # 保存数据
        combined_data.to_csv(filename, index=False)
        print(f"已保存: {filename}")



















