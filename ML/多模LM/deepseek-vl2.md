https://arxiv.org/pdf/2412.10302

1. vision encoder: 用了接收固定大小图片的 SigLIP model。 SigLIP 本身用了2D 绝对位置编码。
2. 怎么支持的任意分辨率图片：
   
![image](https://github.com/user-attachments/assets/5f0b58cc-76ca-4ffa-ab81-adf5c25aabde)

3. 位置编码：图片的位置编码只是用了 vision encoder 里的位置编码。然后LLM 里，仍用 1d-rope。但是用特殊换行符号分隔图片的不同patch 行。
