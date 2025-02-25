# C++ 中怎样做 multinomial 多项分布抽样 

好些情况下，需要从多项分布（multinomial ）中随机抽样。比如RNN序列生成，可能需要从softmax中随机抽样作为下一个时间的输入。

numpy 可以用 np.random.multinomial
```
    sample_cnt = 1
    sm =[0.1, 0.1, ... , 0.1]
    ret = np.random.multinomial(sample_cnt, sm) 
    ret = np.nonzero(ret)[0]
```
tensorflow 中也有相应函数。

C++中，固然可以想办法自己实现，但其实可以直接用 std::discrete_distribution。示例：
```
   unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
   std::default_random_engine generator (seed);
    float probs[] = {...};
   std::discrete_distribution < int > multinomial_distri(probs, probs + sizeof(probs)/sizeof(float));
    for (int i = 0; i <  10; i ++) { // 随机抽样 n 次
       int out = multinomial_distri(*_generator); 
    }
```
