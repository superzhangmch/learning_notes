1. vision encoder 一般用 ViT，用 MLP 桥接到 LLM 上。（llava 开启用 MLP，相比于 BLIP 所用的复杂的 q-former）。vision encoder 上施加 2d-位置编码。
2. 为了支持 input image 是各种分辨率，一种方式是把图片切块成固定大小，然后用 ViT 编码成固定数量 tokens，然后分多个子图灌注给 LLM。另一种（感觉更高雅）的方式是，vit 本身支持变分辨率（根本在于2d 位置编码不是只支持写死的固定长度），然后在 LLM 的位置编码上，能把图片、video 的patch 坐标编码。
3. LLM 集成了 vision 后，仍然用 1d-Rope 位置编码也是能 work 的。这是因为 vision encoder 都有 2D 位置编码，也就是 vision token 已经自带位置编码了。另外有些做法会对 img patch token 的行尾，加一个 换行 token，这样 LLM 也能识别出换行。
4. LLM 集成了 vision 后，用能反映出 patch 坐标的多维位置编码，直观上是更有道理的。qianwen-VL-2 与 2.5 就用到了这样的位置编码。
