在2025年2月24日至28日，DeepSeek举办了“开源周”活动，连续五天开源了以下核心项目：

1. **FlashMLA**：针对Hopper GPU优化的高效MLA（多头潜在注意力）解码内核，专为处理可变长度序列而设计，已投入生产环境。  

2. **DeepEP**：首个用于MoE（混合专家）模型训练和推理的开源EP（专家并行）通信库，支持低精度操作，包括FP8。 

3. **DeepGEMM**：高效矩阵乘法（GEMM）库，旨在提升深度学习模型的计算效率。  

4. **DualPipe**：双向流水线并行算法，包含EPLB（自动平衡GPU负载）和profile-data（训练和推理框架的分析数据），用于优化分布式系统的协同工作。 

5. **3FS**：高性能分布式文件系统，旨在提升数据存储与通信效率。  



另据：https://zhuanlan.zhihu.com/p/26608701724 中图：
![image](https://github.com/user-attachments/assets/0b320e79-c0c4-4c0a-a74c-6a6cf2f12163)

主要关注于： moe 训练、FP8 训练、 MLA-attention、以及分布式训练方案与文件系统方案。
