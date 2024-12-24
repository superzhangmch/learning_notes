# flink 与流式计算

### 数据聚合
----

无疑 flink（或类似东西）是可以做这样的事的：按一定key聚合，在聚合的数据上作某种操作。

除非要单条数据独立的方式处理，否则就是要把数据关联起来：按一定key比如用户关联数据，使得仿佛每个人有自己独立的数据流。然后再被关联的数据上，往往是要作某一种聚合运算。而一聚合，就设计到聚合哪些。流式计算下，数据是源源不断无始无终到来的。为了划分当前时刻把哪些数据包括进来，需要引入水位（watermrk）的概念。

### watermark
----

可以全局一个水位，或者按需在每一个聚合key上有独立的watermark。 watermark 的原理是：之前看到的所有数据的最大数据自身时间戳(业务时间而非process time)，减去一个预定义的等待窗口，就是watermark。新来的数据如果比watermark大，则它会被处理。如果比watermark低，则应该被丢弃，或者走特殊处理流程。

### 其他： flink 小解释

- flink 是 java 的。它通常是一个 java class 的 main 函数内，把所有处理算子组织成一个 DAG 计算图。构建完（只是build，很快执行完），然后就是 run_env.execute(..), 这时候 main 函数开始 block 在这里不动了：因为开始处理数据了。它会一直在那儿（流式，所以也就不会结束）。
- sink：就是存储落盘的地方。
- assignTimestampsAndWatermarks: watermark 要怎么设置。
- .window(…).trigger(…).process(…)：粗略地可以这样理解：window 负责定义聚合的容器，trigger 负责是否该作聚合，从而清空容器，process负责怎么做聚合
- 
