# flink 与流式计算

### 数据聚合
----

无疑 flink（或类似东西）是可以做这样的事的：按一定key聚合，在聚合的数据上作某种操作。

除非要单条数据独立的方式处理，否则就是要把数据关联起来：按一定key比如用户关联数据，使得仿佛每个人有自己独立的数据流。然后再被关联的数据上，往往是要作某一种聚合运算。而一聚合，就设计到聚合哪些。流式计算下，数据是源源不断无始无终到来的。为了划分当前时刻把哪些数据包括进来，需要引入水位（watermrk）的概念。

### watermark
----

可以全局一个水位，或者按需在每一个聚合key上有独立的watermark。 watermark 的原理是：之前看到的所有数据的最大数据自身时间戳 event time (业务时间而非process time)，减去一个预定义的等待窗口，就是watermark。新来的数据如果比watermark大，则它会被处理。如果比watermark低，则应该被丢弃，或者走特殊处理流程。

注意点：

- **水位更新**：负责生成水位的 flink 算子 assignTimestampsAndWatermarks 往往是多实例的，且每个实例分别维护自己的水位。下游算子如果依赖于水位（比如  session window），下游会按 min(上游各实例的水位）得方式得到全局水位并用之 。这时候一个可能问题是，如果某一个上游实例迟迟没数据来，于是它的水位不更新，就把整个数据流block住了。为此，可以  ```assignTimestampsAndWatermarks(WatermarkStrategy.<HealthProfileOriEvent>forBoundedOutOfOrderness(Duration.ofSeconds(X秒)).withTimestampAssigner(...).withIdleness(Duration.ofSeconds(Y)) ``` 的方式，设置 withIdleness 过期时间，如果一个实例 Y 秒没来数据，则跳过它。但是如果只有一个实例，则设置 withIdleness 也没啥用了。
- **session window 关窗时机**：session window 是靠时间间隔切窗的，也就是如果前后  event 时间差别大于某一阈值，则切窗。对于分布式流式系统，当前的切窗算子并不知道数据流的真实时间进度，它只能靠 event time，最终只能靠水位。也就是能关窗（即触发窗口内容聚合）当且仅当水位超过了 window 内最大event time + gap 时才能发生。也就是说，“若一个event到来后 x 时间内没新的 event 来，则触发聚合” 这样一个需求，在 session window + watermark 机制下是没法做到的，它们只能做到如果超时间 x 后有新数据到则关窗。若没新数据到，这个窗户是迟迟没法关闭的。若想做到 “若一个event到来后 x 时间内没新的 event 来，则触发聚合”，只靠 event time 做不到，需要结合 processing time：给 window 弄一个本地时钟的 timer，该时间到，则触发关窗。
- **水位生成位置**：假如你会按用户id作聚合，会恨不得每个用户有自己的水位。实际上这样是不科学的。在计算图中，水位的放置位置应该尽量靠前。特别如果有数据过滤，应该先生成水位再过滤。因为每条数据的event时间戳就仿佛是时钟的滴答声，如果过滤走了，就相当于时钟不滴答了。
- **数据源 Event time 的同步问题**：数据源如果时间不同步，则 Event time 其实可比较性不大。这会导致水位有问题。不同实例负责不同source时，可能导致水位不前进。如果所有源混合打散了，则可能导致水位蹭蹭蹭上涨，漏掉了太多数据。


### 按 window 作数据聚合
----

重点还是 session window，上面已有提及。假设gap实际是 G，它的工作原理是每一条数据来，都分配一个window，时间范围是 start~end=[event-time, event-time+G], 这样哪怕数据乱序，如果及时来到，就会和别的 window 有交叉。有交叉则可以 merge。一旦新的水位生成，各个window 的end时间比水位小的就可以关窗了（无论是否发生了合并）。

负责关窗的类是  Trigger 类：
- 主要的方法： onElement、onProcessingTime、onEventTime、clear、onMerge、canMerge。其中任一数据进来都会执行 onElement，当窗口如前述方式合并时会调用到 merge。按 event time，比较 window.end-time 和水位，从而决定关窗对应 onEventTime。如果定了 local time timer, 则时间到执行到的是 onProcessingTime。
- Trigger 类中，可以自定义 timer 作 复杂操作，有 event time timer 或 processing time  timer 两种。前者时间到调用 onEventTime(), 后者时间到则调用 onProcessingTime()。前者是靠水位触发的虚拟 timer，而后者是本地的真正 timer。


### 其他： flink 小解释
----

- flink 是 java 的。它通常是一个 java class 的 main 函数内，把所有处理算子组织成一个 DAG 计算图。构建完（只是build，很快执行完），然后就是 run_env.execute(..), 这时候 main 函数开始 block 在这里不动了：因为开始处理数据了。它会一直在那儿（流式，所以也就不会结束）。
- sink：就是存储落盘的地方。
- assignTimestampsAndWatermarks: watermark 要怎么设置。
- .window(…).trigger(…).process(…)：粗略地可以这样理解：window 负责定义聚合的容器，trigger 负责是否该作聚合，从而清空容器，process负责怎么做聚合

### 上游
----
不同上游一方面有时间对齐问题。另外，即使同一个上游，对于业务量大需要不同机房不同部署的情况，flink 和上游队列如果分机房部署，那么flink 与上游队列比如 pulsar 怎么连接呢？

一般操作是flink 与 上游之间按机房直接连。这样一个假设就是用户总被打到同一个机房的上游队列，否则下游按窗口聚合就会被搞分裂了。 在现在的负载均衡机制下，用户总被打到同一个机房的上游队列一般是没啥问题的（所有用户访问同一个dns，但是会根据用户ip被路由到不同的实际ip）。

### 和 spark 对比
----

问 AI，答案是当前（2025.01）的最流行数据处理框架是 spark 与 flink。 spark 本质上是一个 batch 处理 系统，所以它处理流式的时候，是通过 micro batch 的方式。而 flink 也能处理  batch，是通过 stream  的方式。 spark 速度较快，一个因素是尽量在内存进行，少了好多读盘落盘。

另外，spark 与 flink 都支持 SQL 方式来使用。对 spark，那时翻译成相应的任务，flink 也差不多是这样（所以 flink 上做 sql，等于是一个永远不接受的SQL）。
