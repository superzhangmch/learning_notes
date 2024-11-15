# 排序评价指标：Precision@K, NDCG@K, MAP, MRR 等的计算

Precision@K, NDCG@K, MAP, MRR 四个IR评价指标的计算，都是对单个query求得值后，取平均。

下面简述怎么算单query上的值：

- 【Precision@K】假设query 下前K个结果中有n个相关结果，返回n/K。如果结果数不够K，补齐到K（补的都是不相关结果）
- 【NDCG@K】 $\sum_{i=1}^k { \frac {2^{r(i)}-1}{log_2(i + 1)}}$ 或 $\sum_{i=1}^k {\frac {r(i))}{log_2(i + 1)}}$ 。r(i) 是结果的相关性得分（比如相关性分了5档，那么就是档位值）
- 【MAP】假设所有相关结果是{ $r_i$ | i = 1..R},  $r_i$ 表示排序中的序号，则返回 $\sum_{i=1}^R \frac i {r_i}$ 。这等价于 $mean(Precision@r_i$ )
- 【MRR】第1个相关结果排序序号的倒数
