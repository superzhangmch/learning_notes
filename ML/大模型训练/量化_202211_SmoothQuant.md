# 《SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models》 https://arxiv.org/pdf/2211.10438

smoothQuant 要解决的问题是：矩阵乘法 XW，X作为上一层的激活，往往有 outlier channel 存在。作者的想法是，把 这些 outlier 取值转移一部分到 W 上。

<img width="770" height="328" alt="image" src="https://github.com/user-attachments/assets/3c461c63-97fe-420d-95c2-2a1259086578" />

更详细阐述：

<img width="1294" height="826" alt="image" src="https://github.com/user-attachments/assets/af949051-0818-44c3-aa41-28f81a607893" />

### 用于 transformer 

如下，除了 norm 层、softmax 之外，都是用 smooth-quant 量化的：

<img width="752" height="500" alt="image" src="https://github.com/user-attachments/assets/7a6c4ea3-e2bf-4648-84d7-26dace055163" />
