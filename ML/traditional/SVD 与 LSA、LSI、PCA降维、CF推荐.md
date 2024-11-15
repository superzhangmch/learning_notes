# SVD 与 LSA/LSI、PCA降维、CF推荐

什么是矩阵 SVD 分解
=============
假设M是一个 $m * n$ 矩阵，那么存在 $M=U E V'$ , 且 U, V 是 $m * m$ 与 $n * n$ 正交矩阵，E 是 $m * n$ 半正定对角矩阵（对角线元素非负）。如果E对角线元素降序排列，那么E是唯一确定的，而 U、V 不唯一。E 对角元素是奇异值， U、V 是奇异向量矩阵, M' 表示转置。

**存在性**：见http://blog.csdn.net/zhongkejingwang/article/details/43053513 ；

**思路**： $M=U E V'$ => $MV=UE$ , 若令 V={ $v_1, v_2, ..., v_n$ } 是 $MM'$ 的正交化的特征向量，则 V 正交，且 $(MV)'(MV)$ 是对角矩阵，因此对 $MV$ 的正交化过程只需令 $Mv_i$ 变为模1即可，即有对角矩阵 $E_1$ 使得 $MVE_1$ 为正交矩阵，令 $U=MVE_1$ , 则存在对角矩阵使得 $MV=(MVE_1)E=UE$ , 得证。

**E排序后唯一性**： $MM'=UEEU'$ , $M'M=V'EEV$ , 故而 $E^2$ 是 $MM'$ 的取值确定特征值，故E取值确定。

SVD特性
======
对于E中非零元素降序排序后，保留top k个而忽略其他取值小的，记为 $E_k$ , 则 $UEV'$ 能近似地还原 M (因此这也算一种数据压缩，也可说是去了noise)。这是U、V分别只有部分能发挥作用，把发挥作用部分记为 $U_k$ , 
 $V_k$ , 则 $U_k E_k V_k'$ ≈ M。实际上这是 M 的最佳 k 秩 L2 范数逼近.

wikipedia：
> when you select the k largest singular values, and their corresponding singular vectors from U and V, you get the rank k approximation to M with the smallest error；

另见：https://nlp.stanford.edu/IR-book/pdf/18lsi.pdf 

SVD应用
======

LSA/LSI 潜语义分析/索引
--------------------------
LSA/LSI 潜语义分析/索引，即用到了SVD。

假设M是一个 m*n term-doc矩阵(每列代表一个doc)。则据 wikipedia， $row_i$ 与 $row_j$ 的点乘其实就代表了不同term之间的一种相关关系， $col_i$ 与 $col_j$ 同理。 $M'M$ 所以也算是一种相关矩阵了。

对于term-doc 矩阵作SVD分解后的意义，在于截取top k个奇异值后(所得对角矩阵记为 $E_k$ )，可以得到row、col的压缩向量表示。 $E_K V_k$ 所得矩阵就是doc向量矩阵，每个doc对应一列； $U_k E_k$ 所得矩阵就是term向量矩阵, 每个doc同样对应一行。这些压缩表示还满足 cosine 距离近的，其语义也更有相关性（所以说是潜在语义）。

另外，在word2vec那样的词向量层面， $U_k$ 、 $V_k$ 就对应term、doc的词向量；而 $U_k E_k ≈ V_k M$ ， $E_K V_k' ≈ M U_k'$ 也可算词向量（从看到的资料，似乎用任一种以计算term-term相关性的都有）。

对于新的term、doc，可以 $U_k$ , $E_k$ , $V_k$ 把它作相应映射，就可以得到对应的压缩向量表示了。

见 https://en.wikipedia.org/wiki/Latent_semantic_analysis

PCA 降维
----------
PCA用于数据降维，基本想法是假设原始数据是不规则分布的（而不是对称球形分布），则可以找到一个新的坐标系，使得逐次各个坐标轴尽量正冲着数据分布的方向（最大化轴上投影方差）。为达到这个目的，首先把原矩阵M调整为0均值。接下来需要求得M'M的特征值以及特征向量，正对应求解 M的svd分解 $UEV'$ 的E和V——所以也可以说对M先做SVD分解得到相应E、V矩阵。然后用V对M作映射MV即得到M的PCA降维结果了。

参： http://deeplearning.stanford.edu/wiki/index.php/主成分分析

协同过滤(CF)推荐
------------------
推荐问题一般归为user-item矩阵的缺失值预测问题。

基于SVD分解的协同过滤，一种方式是对矩阵分解后，取topK奇异值然后作矩阵重建，这时候重点在于缺失值怎么预先填充（预填平均值？还是什么？）。也可以共分解后得到的user/item矩阵计算user/item相关性作user/item-based协同过滤。

SVD分解成本高，且效果并不比后来的各种矩阵分解效果好，所以现在所说的矩阵分解CF，甚至SVD分解的CF，往往并不是原始SVD-CF。只是因为从SVD发展而来（突破点是funk-svd方法），基本思想以及表达形式（可表达为矩阵相乘）差不多，沿用而已。

另外，一般所说的矩阵分解的协同过滤，是分解为两个矩阵，而SVD分解为三个矩阵，实际上若令 $U_1=U \sqrt{E}$ , $V_1=\sqrt{E} V$ ，则 $M=U_1 V_1$ 就是两个矩阵的分解了（有论文就是这样做的一时找不到题目）。所以并不矛盾。

