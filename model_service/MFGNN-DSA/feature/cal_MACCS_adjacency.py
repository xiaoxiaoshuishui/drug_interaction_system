import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform


def calculate_maccs_adjacency(input_file, output_file, threshold=0.5):
    """
    计算 MACCS 指纹的邻接矩阵
    :param input_file: fea_MACCS.py 生成的 drug_MACCS.csv 文件路径
    :param output_file: 输出的邻接矩阵 csv 路径
    :param threshold: 二值化的阈值 (论文中提到 predefined threshold)
    """
    print(f"正在读取文件: {input_file} ...")
    # 1. 读取数据
    # fea_MACCS.py 生成的文件第一列是 'NAME'，作为索引
    try:
        df = pd.read_csv(input_file, index_col='NAME')
    except FileNotFoundError:
        print("错误: 找不到输入文件，请先运行 feature/fea_MACCS.py 生成 drug_MACCS.csv")
        return

    print(f"数据加载成功，包含 {df.shape[0]} 个药物，维度 {df.shape[1]}")
    # 2. 计算成对 Jaccard 相似度
    # 注意：scipy.spatial.distance.pdist 计算的是"Jaccard 距离" (Dissimilarity)
    # Jaccard 距离 = 1 - Jaccard 相似度
    # 所以：相似度 = 1 - 距离
    print("正在计算 Jaccard 相似度矩阵...")
    # df.values 是 0/1 矩阵，metric='jaccard' 专门处理布尔向量
    jaccard_distances = pdist(df.values, metric='jaccard')

    # 将距离向量转换为方阵
    distance_matrix = squareform(jaccard_distances)

    # 转换为相似度矩阵
    similarity_matrix = 1 - distance_matrix

    # 补全对角线（药物与自身的相似度为 1）
    np.fill_diagonal(similarity_matrix, 1.0)

    # 转回 DataFrame 格式，保持药物名称索引
    sim_df = pd.DataFrame(similarity_matrix, index=df.index, columns=df.index)

    # 3. 二值化处理 (Binarization)
    print(f"正在进行二值化处理 (阈值 = {threshold})...")
    # 大于阈值设为 1，否则设为 0
    adj_matrix = (sim_df >= threshold).astype(int)

    # 4. 保存结果
    adj_matrix.to_csv(output_file)
    print(f"计算完成！邻接矩阵已保存至: {output_file}")

    # 打印预览
    print("\n生成的邻接矩阵预览 (前5行5列):")
    print(adj_matrix.iloc[:5, :5])


# --- 使用示例 ---
if __name__ == "__main__":
    # 请确保您已经运行过 fea_MACCS.py 并有了 drug_MACCS.csv
    # 这里假设输入文件在 feature 目录下，您可能需要根据实际路径修改
    input_csv = './drug_MACCS.csv'
    output_csv = 'calculated_Adjacency_matrix_drug_MACCS.csv'

    # 注意：阈值 0.5 是一个假设值，如果您发现生成的矩阵比原作者的稀疏或稠密
    # 可以尝试调整这个值 (例如 0.4 或 0.6)
    calculate_maccs_adjacency(input_csv, output_csv, threshold=0.65)