transformer 之 LLM，生成无疑是接龙方式的。

它的训练虽然是对一个序列，一次训练完，但是本质上是并行式训练的，理论上就是接龙式训出来的。

为什么接龙训，却能有奇效呢？

claude 有对他的解释： https://www.anthropic.com/research/tracing-thoughts-language-model。大体上说，生成时并不是生成下一个token，而是已经想好了接下来怎么做，生成的token不过对提纲的落笔第一字而已。

为啥这样？我觉得首先，它的训练其实并不是独立训的。虽然大家都说是并行，其实不是真的并行，同一个数据的多个token耦合在一起一次训，一定有某种协同作用，使得训第i个token的时候，看似在拟合它，其实暗地里考虑到了后面的token。如果完全不考虑成本，我这样训练：
```
arr = [one_data for one_data in all_training_dataset.select_random(N)]
arr1 = [a[: random(1, len(a)] for a in arr]
total_loss = sum([loss(pred(a[:-1]), a[-1]) for a in arr1]) / N 
```

也就是随机选 N 条数据，每条数据选择预测其中的第r个token，这样构造一个 batch=N的batch，然后训一轮，如此进行。按说也应该可以——这样是真正的下一token 训练。我觉得这样训出的 model 的效果不会很好。
