# transformer 的隐层 shape 是 [B,S,H] 还是 [S,B,H] layout, 啥区别

令 B=batch_size， S=sequence_len, H=hidden_dim, transformer 的 hidden shape，可以有两种选法：[B,S,H] (batch first) 或 [S,B,H] (sequence first)。

对于 transformer 来说：
- 只有 softmax(QK')V' 这一步真正涉及序列操作，从而 [B,S,H]、[S,B,H] 有区别。
- 其他地方，包括 attn 的 projection、FNN、layerNorm 等，[B,S,H]、[S,B,H] 没区别：它们都是 token 粒度计算的，本质上 batch_size=B*S。 

先记下结论：无论用哪种，当前（2025.08.17) transformer 计算 attn 时，**都是用的 [B,S,H]**, 形式，如果不是，则先转成。

RNN 时代都是 [S, B, H] 形式的（RNN/LSTM/GRU 模块）。transformer 时代，两者都有用，主流是 [B,S,H]，而 megatron 是用的 [S,B,H] （但内部 attn 会转成 [B, S, H]）。

----

### （1）、torch.nn.MultiheadAttention: 最终用 [B, S, H]

它默认把 input 当 batch_first=False （[S, B, H] 处理。看代码，如果不是，也会先转成 [S,B,H]。但是到了做真正做 MHA 的时候，还是会转 [B,S,H]）:

<img width="1368" height="600" alt="image" src="https://github.com/user-attachments/assets/233f5a9a-b626-453d-8032-f3b58c4ea689" />

### (2)、flashAttention：用 [B, S, H]

###（3）、megatron： attn 用 [B, S, H]

megatron 在其他地方都用的 [S, B, H], 但是 attn 仍然用的 [B, S, H]。

