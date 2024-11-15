# GBDT、CART与categorical特征

CART 决策树（GBDT基于CART）的构建，在于能能对特征数据按某种规则作分裂，作split。

对于连续类型的特征，只需找到一个分裂点，自然就分成两半了。即使是连续特征，在样本数固定的情况下，其实只有有限种取值，所以候选切分点一般选用所有实际取值排序后相邻两个元素的中点。这时候最坏情况是切分点和样本数一样。

对于类别（categorical）类型的特征，没有序的概念，想要split，只能是对于该特征的所有取值集合作集合拆分。假设有 n 种取值，那么拆分方案有 $2^{n-1}$ 种，要在这么多种方案中取最优，显然是几乎不可能的。因此，决策树在处理categorical特征的时候，是没那么轻松的，需要想着法子来作。(注意：有序categorical可当连续看待)

一种方式当然是可以把类别特征one-hot编码化。如果编码化后维度太高，恐怕会不好处理。catboost、LightGBM等GB树实现号称可以直接处理categorical特征，不过不清楚他们怎么做的。

【参考】
- https://tech.yandex.com/catboost/doc/dg/concepts/algorithm-main-stages_cat-to-numberic-docpage/
- https://tech.yandex.com/catboost/doc/dg/concepts/parameter-tuning_ctr-docpage/
- https://github.com/Microsoft/LightGBM/issues/699
- http://www.dansteinbergblog.com/dan-steinberg/modeling-tricks-with-treenet-treating-categorical-variables-as-continuous
- https://github.com/Microsoft/LightGBM/blob/master/docs/Quick-Start.md
- https://stats.stackexchange.com/questions/152433/will-decision-trees-perform-splitting-of-nodes-by-converting-categorical-values
- https://cn.mathworks.com/help/stats/splitting-categorical-predictors-for-multiclass-classification.html
