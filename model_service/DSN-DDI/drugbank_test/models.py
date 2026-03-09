import torch

from torch import nn
import torch.nn.functional as F
from torch.nn.modules.container import ModuleList
from torch_geometric.nn import (
                                GATConv,
                                SAGPooling,
                                LayerNorm,
                                global_add_pool,
                                Set2Set,
                                )

from layers import (
                    CoAttentionLayer, 
                    RESCAL, 
                    IntraGraphAttention,
                    InterGraphAttention,
                    )
import time




class MVN_DDI(nn.Module):
    def __init__(self, in_features, hidd_dim, kge_dim, rel_total, heads_out_feat_params, blocks_params):
        super().__init__()
        self.in_features = in_features
        self.hidd_dim = hidd_dim
        self.rel_total = rel_total
        self.kge_dim = kge_dim
        self.n_blocks = len(blocks_params)
        
        self.initial_norm = LayerNorm(self.in_features)
        self.blocks = []
        self.net_norms = ModuleList()
        for i, (head_out_feats, n_heads) in enumerate(zip(heads_out_feat_params, blocks_params)):
            block = MVN_DDI_Block(n_heads, in_features, head_out_feats, final_out_feats=self.hidd_dim)
            self.add_module(f"block{i}", block)
            self.blocks.append(block)
            self.net_norms.append(LayerNorm(head_out_feats * n_heads))
            in_features = head_out_feats * n_heads
        
        self.co_attention = CoAttentionLayer(self.kge_dim)
        self.KGE = RESCAL(self.rel_total, self.kge_dim)

    def forward(self, triples):
        h_data, t_data, rels, b_graph = triples

        h_data.x = self.initial_norm(h_data.x, h_data.batch)
        t_data.x = self.initial_norm(t_data.x, t_data.batch)
        repr_h = []
        repr_t = []

        for i, block in enumerate(self.blocks):
            out = block(h_data,t_data,b_graph)

            h_data = out[0]
            t_data = out[1]
            r_h = out[2]
            r_t = out[3]
            repr_h.append(r_h)
            repr_t.append(r_t)
        
            h_data.x = F.elu(self.net_norms[i](h_data.x, h_data.batch))
            t_data.x = F.elu(self.net_norms[i](t_data.x, t_data.batch))
        
        repr_h = torch.stack(repr_h, dim=-2)
        repr_t = torch.stack(repr_t, dim=-2)
        kge_heads = repr_h
        kge_tails = repr_t
        # print(kge_heads.size(), kge_tails.size(), rels.size())
        attentions = self.co_attention(kge_heads, kge_tails)
        # attentions = None
        scores = self.KGE(kge_heads, kge_tails, rels, attentions)
        return scores     

#intra+inter
class MVN_DDI_Block(nn.Module):
    def __init__(self, n_heads, in_features, head_out_feats, final_out_feats):
        super().__init__()
        self.n_heads = n_heads
        self.in_features = in_features
        self.out_features = head_out_feats

        self.feature_conv = GATConv(in_features, head_out_feats, n_heads)
        self.intraAtt = IntraGraphAttention(head_out_feats*n_heads)
        self.interAtt = InterGraphAttention(head_out_feats*n_heads)
        self.readout = SAGPooling(n_heads * head_out_feats, min_score=-1)
    
    def forward(self, h_data,t_data,b_graph):
     
        h_data.x = self.feature_conv(h_data.x, h_data.edge_index)
        t_data.x = self.feature_conv(t_data.x, t_data.edge_index)
   
        h_intraRep = self.intraAtt(h_data)
        t_intraRep = self.intraAtt(t_data)
        
        h_interRep,t_interRep = self.interAtt(h_data,t_data,b_graph)
        
        h_rep = torch.cat([h_intraRep,h_interRep],1)
        t_rep = torch.cat([t_intraRep,t_interRep],1)
        h_data.x = h_rep
        t_data.x = t_rep

        
        # readout
        h_att_x, att_edge_index, att_edge_attr, h_att_batch, att_perm, h_att_scores= self.readout(h_data.x, h_data.edge_index, batch=h_data.batch)
        t_att_x, att_edge_index, att_edge_attr, t_att_batch, att_perm, t_att_scores= self.readout(t_data.x, t_data.edge_index, batch=t_data.batch)
      
        h_global_graph_emb = global_add_pool(h_att_x, h_att_batch)
        t_global_graph_emb = global_add_pool(t_att_x, t_att_batch)
        

        return h_data,t_data, h_global_graph_emb,t_global_graph_emb

# class MVN_DDI_Block(nn.Module):
#     def __init__(self, n_heads, in_features, head_out_feats, final_out_feats):
#         super().__init__()
#         self.n_heads = n_heads
#         self.in_features = in_features
#         self.out_features = head_out_feats
#
#         # 原有的网络层
#         self.feature_conv = GATConv(in_features, head_out_feats, n_heads)
#         self.intraAtt = IntraGraphAttention(head_out_feats * n_heads)
#         self.interAtt = InterGraphAttention(head_out_feats * n_heads)
#         self.readout = SAGPooling(n_heads * head_out_feats, min_score=-1)
#
#         # ==================== 修改部分 1: 动态特征门控 ====================
#         # intra_rep 和 inter_rep 拼接后的维度
#         combined_dim = head_out_feats * n_heads
#         # 定义一个简单的门控网络，输出与拼接后维度相同的权重（0~1之间）
#         self.gate_layer = nn.Sequential(
#             nn.Linear(combined_dim, combined_dim),
#             nn.Sigmoid()
#         )
#         # ===============================================================
#
#         # ==================== 修改部分 2: 残差连接 ====================
#         # 因为输入特征 in_features 与融合后特征 combined_dim 的维度可能不同，
#         # 需要一个线性层来进行维度对齐，以便后面进行矩阵相加
#         self.res_proj = nn.Linear(in_features, combined_dim)
#         # ===============================================================
#
#     def forward(self, h_data, t_data, b_graph):
#         # ==================== 修改部分 2: 残差连接 ====================
#         # 保存最初始的输入特征，用于后面的残差相加
#         h_residual = h_data.x
#         t_residual = t_data.x
#         # ===============================================================
#
#         # GAT 卷积特征提取 (维度变化: in_features -> head_out_feats * n_heads)
#         h_data.x = self.feature_conv(h_data.x, h_data.edge_index)
#         t_data.x = self.feature_conv(t_data.x, t_data.edge_index)
#
#         # 内部图特征提取
#         h_intraRep = self.intraAtt(h_data)
#         t_intraRep = self.intraAtt(t_data)
#
#         # 外部图特征提取
#         h_interRep, t_interRep = self.interAtt(h_data, t_data, b_graph)
#
#         # ==================== 修改部分 1: 动态特征门控 ====================
#         # Head (头实体) 的特征门控融合
#         h_cat = torch.cat([h_intraRep, h_interRep], 1)  # 先进行拼接
#         h_gate = self.gate_layer(h_cat)  # 计算门控权重
#         h_rep = h_cat * h_gate  # 将权重乘回拼接后的特征，进行自适应过滤
#
#         # Tail (尾实体) 的特征门控融合
#         t_cat = torch.cat([t_intraRep, t_interRep], 1)
#         t_gate = self.gate_layer(t_cat)
#         t_rep = t_cat * t_gate
#         # ===============================================================
#
#         # ==================== 修改部分 2: 残差连接 ====================
#         # 将原始输入特征经过维度对齐(res_proj)后，加到最终提取的特征(h_rep)上
#         # 这里加上了一个激活函数 F.elu() 增加非线性表达能力
#         h_data.x = F.elu(h_rep + self.res_proj(h_residual))
#         t_data.x = F.elu(t_rep + self.res_proj(t_residual))
#         # ===============================================================
#
#         # readout 层 (池化与全局图嵌入生成)，保持原逻辑不变
#         h_att_x, att_edge_index, att_edge_attr, h_att_batch, att_perm, h_att_scores = self.readout(h_data.x,
#                                                                                                    h_data.edge_index,
#                                                                                                    batch=h_data.batch)
#         t_att_x, att_edge_index, att_edge_attr, t_att_batch, att_perm, t_att_scores = self.readout(t_data.x,
#                                                                                                    t_data.edge_index,
#                                                                                                    batch=t_data.batch)
#
#         h_global_graph_emb = global_add_pool(h_att_x, h_att_batch)
#         t_global_graph_emb = global_add_pool(t_att_x, t_att_batch)
#
#         return h_data, t_data, h_global_graph_emb, t_global_graph_emb



