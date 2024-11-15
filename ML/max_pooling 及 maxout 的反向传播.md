# max_pooling 及 maxout 的反向传播

max_pooling/maxout 层怎样做反向传播？做法是只把上一层传过来的误差传给本层的 max 操作的 winner，非winner 只传 0。

实际上， $max(x,y)=\frac {x+y+|x-y|}2$ , 是分段可导的。max_pooling 可以作为 max 的组合，也是分段可导的。而maxout 就是 max，当然也分段可导。
而分段可导函数，比如relu，leak-relu, 都是可以反向传播的。故max_pooling, maxout当然可以反向传播。

【参】
- https://www.quora.com/How-are-gradients-computed-through-max-pooling-or-maxout-units-in-neural-networks
- https://www.reddit.com/r/MachineLearning/comments/2vl8hp/a_question_about_maxout_who_gets_the_error/
