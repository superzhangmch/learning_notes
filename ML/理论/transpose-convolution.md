transpose-conv（转置卷积）用于升维。以一个例子来说明它是怎么算的：

> 假设是要做  1d-transpose-conv：input = [a, b, c, d, e], kernel=[w1, w2, w3], stride=1, output=?

答案是：
```
output = 
[ a*w1, a*w2, a*w3, 0,    0,    0,    0] +
[ 0,    b*w1, b*w2, b*w3, 0,    0,    0] +
[ 0,    0,    c*w1, c*w2, c*w3, 0,    0] +
[ 0,    0,    0,    d*w1, d*w2, d*w3, 0] +
[ 0,    0,    0,    0,    e*w1, e*w2, e*w3]
```

或者拆解如下。下面用纵向表格表示，每一行是 input 的一个元素，每一列是 output 的一个位置。对应的 cell 表示该 input 元素对该 output 位置的贡献（没有贡献则空着）。

| input  | output[0] | output[1]   | output[2]         | output[3]         | output[4]         | output[5]   | output[6] |
|--------|-----------|-------------|-------------------|-------------------|-------------------|-------------|-----------|
| **a**  | a×w1      | a×w2        | a×w3              |                   |                   |             |           |
| **b**  |           | b×w1        | b×w2              | b×w3              |                   |             |           |
| **c**  |           |             | c×w1              | c×w2              | c×w3              |             |           |
| **d**  |           |             |                   | d×w1              | d×w2              | d×w3        |           |
| **e**  |           |             |                   |                   | e×w1              | e×w2        | e×w3      |

每一列竖着加，就是对应的 output 元素：

- output[0] = a×w1
- output[1] = a×w2 + b×w1
- output[2] = a×w3 + b×w2 + c×w1
- output[3] = b×w3 + c×w2 + d×w1
- output[4] = c×w3 + d×w2 + e×w1
- output[5] = d×w3 + e×w2
- output[6] = e×w3

也就是说对于 input 的一个元素和 conv kernel 的所有元素相乘(即 $a_{ij} \cdot M_{kernel}$ ，数字乘矩阵), 把乘积结果和最终结果矩阵找好对应关系，往结果矩阵上累加即可。

----

既然 transpose-conv 就是单点乘kernel，**恰当**散布到结果矩阵后累加。那么怎么恰当散布呢？ 可以参  https://arxiv.org/pdf/1603.07285 ， P25：

stride=1：

![image](https://github.com/user-attachments/assets/591aeb5d-0654-4df7-bd43-3d89382acd8c)

如果 stride > 1, 则 $a_{ij} \cdot M_{kernel}$ 要按 stride 跳着移动。

![image](https://github.com/user-attachments/assets/21b80db1-98bf-4823-932f-ce27bbf345e9)

----

### 为什么称为 transpose?

根据 https://zhuanlan.zhihu.com/p/549164774 ，实际操作的时候：

（1）、如果是普通卷积，则展开成：

![image](https://github.com/user-attachments/assets/87046d79-ec50-4c0a-8525-a40d501795a5)

（2）、如果是transpose 卷积，则展开后是（kernel 展开矩阵正巧是普通conv 的转置）：

![image](https://github.com/user-attachments/assets/928f05bb-8c0d-433a-aec4-ad19cee71966)
