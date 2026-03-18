import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import networkx as nx
import random
from tqdm import tqdm

# =================配置=================
EMBEDDING_DIM = 128  # 嵌入维度
WALK_LENGTH = 10  # 随机游走长度
WALKS_PER_NODE = 5  # 每个节点游走次数
WINDOW_SIZE = 3  # Skip-gram窗口大小
BATCH_SIZE = 1024  # 批大小
EPOCHS = 10  # 训练轮数
LR = 0.001  # 学习率


# =================1. 异构图构建=================
def build_simple_hin():
    """
    构建异构网络：
    节点：Drug, Disease, SideEffect
    边：Drug-Disease, Drug-SideEffect
    """
    print("构建简化的异构图...")

    # 读取药物、疾病、副作用列表
    try:
        drugs_df = pd.read_csv('../data/drug.csv')
        diseases_df = pd.read_csv('../data/disease.csv')
        ses_df = pd.read_csv('../data/se.csv')

        drugs = drugs_df.iloc[:, 0].astype(str).tolist()
        diseases = diseases_df.iloc[:, 0].astype(str).tolist()
        ses = ses_df.iloc[:, 0].astype(str).tolist()
    except Exception as e:
        print(f"读取节点文件失败: {e}")
        # 使用示例数据
        drugs = [f"Drug_{i}" for i in range(100)]
        diseases = [f"Dis_{i}" for i in range(50)]
        ses = [f"SE_{i}" for i in range(200)]

    # 创建节点映射
    node_list = drugs + diseases + ses
    node2id = {node: i for i, node in enumerate(node_list)}
    id2node = {i: node for i, node in enumerate(node_list)}

    # 记录类型范围
    num_drugs = len(drugs)
    num_diseases = len(diseases)
    drug_ids = list(range(num_drugs))
    disease_ids = list(range(num_drugs, num_drugs + num_diseases))
    se_ids = list(range(num_drugs + num_diseases, len(node_list)))

    # 构建网络
    G = nx.Graph()

    # 添加节点
    for node_id, node_name in id2node.items():
        if node_id < num_drugs:
            node_type = 'drug'
        elif node_id < num_drugs + num_diseases:
            node_type = 'disease'
        else:
            node_type = 'side_effect'
        G.add_node(node_id, type=node_type, name=node_name)

    # 添加Drug-Disease边
    try:
        print(f"尝试读取文件: ../data/mat_drug_disease.csv")
        mat_dd = pd.read_csv('../data/mat_drug_disease.csv', header=None, low_memory=False)
        print(f"成功读取! 形状: {mat_dd.shape}")

        # 检查是否需要跳过第一行和第一列（标签行/列）
        has_labels = False

        # 检查第一行第一列是否为字符串（可能是标签）
        if isinstance(mat_dd.iloc[0, 0], str) or pd.isna(mat_dd.iloc[0, 0]):
            has_labels = True
            print("检测到第一行和第一列为标签行/列，跳过...")

        if has_labels:
            # 跳过第一行和第一列
            for i in range(1, min(len(drugs) + 1, mat_dd.shape[0])):
                for j in range(1, min(len(diseases) + 1, mat_dd.shape[1])):
                    try:
                        # 尝试转换为数值
                        value = float(mat_dd.iloc[i, j])
                        if value > 0:  # 有关联
                            drug_id = i - 1  # 减去标签行偏移
                            disease_id = num_drugs + (j - 1)  # 减去标签列偏移
                            G.add_edge(drug_id, disease_id, relation='drug-disease')
                    except (ValueError, TypeError):
                        # 如果不能转换为数值，跳过
                        continue
        else:
            # 原始逻辑（没有标签行/列）
            for i in range(min(len(drugs), mat_dd.shape[0])):
                for j in range(min(len(diseases), mat_dd.shape[1])):
                    try:
                        value = float(mat_dd.iloc[i, j])
                        if value > 0:  # 有关联
                            drug_id = i
                            disease_id = num_drugs + j
                            G.add_edge(drug_id, disease_id, relation='drug-disease')
                    except (ValueError, TypeError):
                        continue

        print(f"添加了 {G.number_of_edges()} 条边")

    except Exception as e:
        print(f"读取Drug-Disease关联失败，具体错误: {e}")
        print("使用示例Drug-Disease关联")
        # 示例关联：每个药物关联2-3个疾病
        for drug_id in drug_ids[:min(20, len(drug_ids))]:
            for _ in range(random.randint(2, 3)):
                disease_id = random.choice(disease_ids)
                G.add_edge(drug_id, disease_id, relation='drug-disease')

    # 添加Drug-SideEffect边
    try:
        mat_dse = pd.read_csv('../data/mat_drug_se.csv', header=None)
        for i in range(min(len(drugs), mat_dse.shape[0])):
            for j in range(min(len(ses), mat_dse.shape[1])):
                if mat_dse.iloc[i, j] > 0:
                    drug_id = i
                    se_id = num_drugs + num_diseases + j
                    G.add_edge(drug_id, se_id, relation='drug-se')
    except:
        print("使用示例Drug-SE关联")
        # 示例关联：每个药物关联5-10个副作用
        for drug_id in drug_ids[:min(20, len(drug_ids))]:
            for _ in range(random.randint(5, 10)):
                se_id = random.choice(se_ids)
                G.add_edge(drug_id, se_id, relation='drug-se')

    print(f"图构建完成: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
    return G, node2id, id2node, drug_ids, se_ids


# =================2. 基于元路径的随机游走=================
def meta_path_random_walk(G, start_node, meta_path):
    """
    基于元路径的随机游走
    meta_path: 例如 ['drug', 'disease', 'drug', 'side_effect']
    """
    path = [start_node]
    current = start_node
    current_type = G.nodes[current]['type']

    for target_type in meta_path[1:]:  # 从第二个类型开始
        # 找到当前节点的邻居中符合目标类型的节点
        neighbors = [n for n in G.neighbors(current)
                     if G.nodes[n]['type'] == target_type]

        if not neighbors:
            break  # 如果没有符合的邻居，终止游走

        # 随机选择一个邻居
        next_node = random.choice(neighbors)
        path.append(next_node)
        current = next_node
        current_type = target_type

    return path


# =================3. 生成训练数据（分批处理）=================
def generate_training_corpus(G, meta_paths):
    """
    生成Word2Vec训练语料（随机游走路径）
    分批生成，避免内存爆炸
    """
    print("生成随机游走语料...")

    corpus = []
    nodes = list(G.nodes())

    for _ in range(WALKS_PER_NODE):
        random.shuffle(nodes)
        for node in tqdm(nodes, desc="随机游走"):
            # 随机选择一个元路径
            meta_path = random.choice(meta_paths)

            # 生成基于元路径的随机游走
            walk = meta_path_random_walk(G, node, meta_path)

            if len(walk) > 1:  # 至少有两个节点
                # 将节点ID转换为字符串（Word2Vec需要字符串）
                walk_str = [str(node_id) for node_id in walk]
                corpus.append(walk_str)

    return corpus


# =================4. 训练Word2Vec模型=================
def train_word2vec_embeddings(corpus, vocab_size, embedding_dim):
    """
    使用gensim的Word2Vec训练节点嵌入
    """
    print("训练Word2Vec模型...")

    try:
        from gensim.models import Word2Vec

        # 训练Word2Vec模型
        model = Word2Vec(
            sentences=corpus,
            vector_size=embedding_dim,
            window=WINDOW_SIZE,
            min_count=1,  # 所有节点都出现
            sg=1,  # Skip-gram模型
            workers=4,
            epochs=EPOCHS
        )

        # 获取嵌入矩阵
        embedding_matrix = np.zeros((vocab_size, embedding_dim))
        for i in range(vocab_size):
            if str(i) in model.wv:
                embedding_matrix[i] = model.wv[str(i)]
            else:
                # 如果没有该节点的嵌入，使用随机初始化
                embedding_matrix[i] = np.random.randn(embedding_dim) * 0.01

        return embedding_matrix, model

    except ImportError:
        print("未安装gensim")
        return None, None

def main():
    print("=" * 50)
    print("简化版HIN2Vec - 异构网络节点嵌入")
    print("=" * 50)

    # 1. 构建异构图
    G, node2id, id2node, drug_ids, se_ids = build_simple_hin()
    vocab_size = len(node2id)

    # 2. 定义元路径
    # 这些元路径捕获异构网络中的语义关系
    meta_paths = [
        ['drug', 'disease', 'drug'],  # 共享疾病的药物
        ['drug', 'side_effect', 'drug'],  # 共享副作用的药物
        ['side_effect', 'drug', 'side_effect'],  # 共享药物的副作用
        ['drug', 'disease', 'drug', 'side_effect'],  # 药物-疾病-药物-副作用
        ['side_effect', 'drug', 'disease', 'drug'],  # 副作用-药物-疾病-药物
    ]

    # 3. 生成训练语料
    corpus = generate_training_corpus(G, meta_paths)
    print(f"生成 {len(corpus)} 条随机游走路径")

    # 4. 训练嵌入
    embedding_matrix, w2v_model = train_word2vec_embeddings(
        corpus, vocab_size, EMBEDDING_DIM
    )

    # 5. 提取并保存药物和副作用嵌入
    print("提取药物和副作用嵌入...")

    # 药物嵌入
    drug_embeddings = embedding_matrix[drug_ids]
    drug_names = [id2node[i] for i in drug_ids]

    # 副作用嵌入
    # 副作用嵌入 - 修复越界问题
    valid_se_ids = []
    for sid in se_ids:
        if sid < embedding_matrix.shape[0]:
            valid_se_ids.append(sid)
        else:
            print(f"警告: 副作用ID {sid} 越界，已跳过")

    if len(valid_se_ids) == 0:
        print("错误: 没有有效的副作用ID")
        # 可以创建一个空数组或退出
        se_embeddings = np.zeros((0, EMBEDDING_DIM))
    else:
        se_embeddings = embedding_matrix[valid_se_ids]

    se_names = [id2node[i] for i in valid_se_ids]

    # 6. 保存为CSV
    print("保存嵌入向量...")

    # 药物嵌入
    drug_df = pd.DataFrame(drug_embeddings, index=drug_names)
    drug_df.index.name = 'NAME'
    drug_df.columns = [f'feat_{i}' for i in range(EMBEDDING_DIM)]
    drug_df.to_csv('./simple_drug_hin.csv')
    print(f"药物嵌入保存至: ./simple_drug_hin.csv")
    print(f"形状: {drug_df.shape}")

    # 副作用嵌入
    se_df = pd.DataFrame(se_embeddings, index=se_names)
    se_df.index.name = 'NAME'
    se_df.columns = [f'feat_{i}' for i in range(EMBEDDING_DIM)]
    se_df.to_csv('./simple_se_hin.csv')
    print(f"副作用嵌入保存至: ./simple_se_hin.csv")
    print(f"形状: {se_df.shape}")

    # 7. 验证嵌入质量
    print("\n嵌入质量验证:")
    print("1. 药物嵌入示例:")
    print(f"   维度: {drug_embeddings.shape[1]}")
    print(f"   数量: {drug_embeddings.shape[0]}")
    print(f"   均值: {drug_embeddings.mean():.4f}")
    print(f"   标准差: {drug_embeddings.std():.4f}")

    print("\n2. 副作用嵌入示例:")
    print(f"   维度: {se_embeddings.shape[1]}")
    print(f"   数量: {se_embeddings.shape[0]}")
    print(f"   均值: {se_embeddings.mean():.4f}")
    print(f"   标准差: {se_embeddings.std():.4f}")

    print("\n3. 相似度计算示例:")
    if w2v_model is not None:
        # 计算最相似的药物
        try:
            sample_drug = drug_names[0]
            similar = w2v_model.wv.most_similar(str(drug_ids[0]), topn=3)
            print(f"   药物 '{sample_drug}' 的最相似节点:")
            for node_id, similarity in similar:
                node_name = id2node[int(node_id)]
                node_type = G.nodes[int(node_id)]['type']
                print(f"     {node_name} ({node_type}): {similarity:.4f}")
        except:
            print("   相似度计算跳过")

    print("\n✅ 简化版HIN2Vec完成！")
    return drug_embeddings, se_embeddings, drug_names, se_names


if __name__ == "__main__":
    try:
        drug_embeddings, se_embeddings, drug_names, se_names = main()
        print("\n✅ HIN2Vec执行成功！")
        print(f"生成文件：")
        print(f"  - simple_drug_hin.csv ({len(drug_names)}个药物)")
        print(f"  - simple_se_hin.csv ({len(se_names)}个副作用)")
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback

        traceback.print_exc()