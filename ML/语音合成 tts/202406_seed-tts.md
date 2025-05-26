# seed-tts https://arxiv.org/abs/2406.02430 《Seed-TTS: A Family of High-Quality Versatile Speech Generation Models》

seed-tts 用了两种方式来做的 tts：
- 经过 speech tokens：text ==(自回归)=> speech_tokens ==(扩散模型)=> mel谱 ==(vocoder)=> audio_wave
- 不经 speech tokens：text ==（扩散模型) => mel谱 ==(vocoder)=> audio_wave

### 经过 speech tokens：text => speech tokens => mel 谱 => audio

![image](https://github.com/user-attachments/assets/361e6275-85b1-4953-be0b-98222c677414)

### 不经 speech tokens：text => mel谱 => audio_wave


参考：https://www.zhihu.com/question/26815523/answer/64177908707

---

## 参考：TorToise-tts： 2023.05 https://arxiv.org/pdf/2305.07243 《Better speech synthesis through scaling》

比它更早的 tortoise-TTS，无疑给了 seed-tts 很大的启发。tortroise-tts 就差不多是 `text ==(自回归)=> speech_tokens ==(扩散模型)=> mel谱 ==(vocoder)=> audio_wave` 模式的，除了没用 speech_tokens而是用了激活前的 latent。它的 speech tokens 的获取方式是：对 mel谱作 vqvae，从而得到 8192 个 audio tokens。

![image](https://github.com/user-attachments/assets/84d9e5df-da58-4caa-935e-f9eae642fe39)

CLVP（audio-text相关性model） 类似于 CLIP。生成多个用 CLVP 优选一个，是用的 delle的思路。如果忽略它，则是：

![image](https://github.com/user-attachments/assets/ad08995d-acd5-4487-ab10-f9355d17a31d)
