1. vision encoder 一般用 ViT，用 MLP 桥接到 LLM 上。（llava 开启用 MLP，相比于 BLIP 所用的复杂的 q-former）。vision encoder 上施加 2d-位置编码。
2. 为了支持 input image 是各种分辨率，一种方式是（比如 deepseek-VL-2）把图片切块成固定大小，然后用 ViT 编码成固定数量 tokens，然后分多个子图灌注给 LLM。另一种（感觉更高雅）的方式是，vit 本身支持变分辨率（根本在于2d 位置编码不是只支持写死的固定长度）基础上，LLM 的位置编码也能关注到图片、video 的patch 坐标。
3. LLM 集成了 vision 后，仍然用 1d-Rope 位置编码也是能 work 的。这是因为 vision encoder 都有 2D 位置编码，也就是 vision token 已经自带位置编码了。另外有些做法会对 img patch token 的行尾，加一个 换行 token，这样 LLM 也能识别出换行。
4. LLM 集成了 vision 后，用能反映出 patch 坐标的多维位置编码，直观上是更有道理的。qianwen-VL-2 与 2.5 就用到了这样的位置编码。

另外，在《EVE series2》https://arxiv.org/pdf/2502.06788 中看到的这张图不错，讲了 VLM 的各种方案：

![image](https://github.com/user-attachments/assets/57b97726-a7f4-445c-b09e-c4157b35af23)
