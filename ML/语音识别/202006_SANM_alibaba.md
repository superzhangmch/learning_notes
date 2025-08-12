# 《SAN-M: Memory Equipped Self-Attention for End-to-End Speech Recognition》 https://arxiv.org/pdf/2006.01713

 
<img width="982" height="1284" alt="image" src="https://github.com/user-attachments/assets/a2fe949d-199d-4b6d-b1a8-04dffd9931a4" />

Memory Block 即：DFSMN=deep feed-forward sequential memory network

https://modelscope.cn/models/iic/speech_sanm_kws_phone-xiaoyun-commands-online/summary 这个小 asr model 就用到它。

---

另外参：

- 《Streaming Chunk-Aware Multihead Attention for Online End-to-End Speech Recognition》 https://arxiv.org/abs/2006.01712

---

### 知识补充：FSMN

参 https://zhuanlan.zhihu.com/p/327906427

FSMN 有点像是 RNN 一样的东西。不过它不是 $h_t = f(x_t, history)$，而是 h_t 根据当前 step 就能独立算出（而不用 RNN 那样迭代算出）。然后把这些前后历史 {h_i} 作加权和，当做当前时间的 context 表示，用于本 step 的计算：融合方式可以是如图这样的 proj 后求和。

<img width="1012" height="720" alt="image" src="https://github.com/user-attachments/assets/732ff4d5-6563-49fb-8cb3-1b3a9431fc27" />

所谓 DFSMN=D+FSMN，其实就是好多 个 FSMN 上下摞起来。但是要用残差把这些 FSMN 连接：

<img width="828" height="734" alt="image" src="https://github.com/user-attachments/assets/9a1ee459-12e6-461a-b266-57b8550b936a" />
