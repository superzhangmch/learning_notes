# 特征工程之：计数特征与 likelihood 特征

对于 categorical 特征，我们有时需要对它作一些统计，得到统计特征。

### 计数特征

一种方式是对特征计数，统计feature value 出现的次数，或在某个类下的出现次数。这样可以当数值特征用，也可以必要的时候把不同的次数当做独立的特征(比如所有出现次数小于10的feature value，可以按次数分为10个特征)。

【参考】
1. https://blogs.technet.microsoft.com/machinelearning/2015/11/03/using-azure-ml-to-build-clickthrough-prediction-models/
2. https://blogs.technet.microsoft.com/machinelearning/2015/02/17/big-learning-made-easy-with-counts/
3. https://msdn.microsoft.com/en-us/library/azure/dn913056.aspx

### likelihood 特征

还有一种方式是统计得到 feature value 在预测目标分类（若是回归问题，则用统计得到的均值）上的经验概率，以此作为数值特征取代原value。这样的处理方法一般称为 likelihood coded 特征，或曰 impact coding feature 或 target coding feature。如果用简单统计的经验概率值，容易出现取值偏差，导致过拟合。实际做法一般是用2重交叉验证的方式：对于数据集拆分为n个交叉验证集，每个 fold 上的 likelihood 特征值采用其余数据（余下的n-1折数据）上的经验概率；而这个经验概率病不是简单统计，而是对该n-1折的数据重新拆分为m折交叉验证——然后每次取不同的m-1份数据统计得经验概率，最后把这m份数据取平均。

【参考】
1. https://datascience.stackexchange.com/questions/11024/encoding-categorical-variables-using-likelihood-estimation
2. https://www.kaggle.com/anokas/time-travel-eda
3. https://www.kaggle.com/tnarik/likelihood-encoding-of-categorical-features
4. http://www.montis.pmf.ac.me/vol32/15.pdf
