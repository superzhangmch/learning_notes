# seed-tts https://arxiv.org/abs/2406.02430 《Seed-TTS: A Family of High-Quality Versatile Speech Generation Models》

seed-tts 用了两种方式来做的 tts：
- 经过 speech tokens：text ==(自回归)=> speech_tokens ==(扩散模型)=> mel谱 ==(vocoder)=> audio_wave
  - 更早的《TorToise-tts》就是差不多这样做的
  - 当前主流 audio_LLM 基本都是这样方式生成的 audio
- 不经 speech tokens（seed-TTS_DiT)：text ==（扩散模型) => mel谱 ==(vocoder)=> audio_wave
  - 该文内作语音转换（voice conversion），差不多也是用的该思路

### （1）、经过 speech tokens：text => speech tokens => mel 谱 => audio

这一步用到了自回归model。但是不像 cosyvoice2：后者直接用的预训练的通用 LM qianwen-0.5B。

![image](https://github.com/user-attachments/assets/361e6275-85b1-4953-be0b-98222c677414)

### （2）、不经 speech tokens(名之为 seed_TTS_DiT)：text => mel谱 => audio_wave

![image](https://github.com/user-attachments/assets/cf39c671-dfb3-41c5-80d4-9e7f021239d3)

对于一句希望作 tts 的 text，最终的 audio 时间长度可长可短。怎么决定呢？如果是"经过speech tokens"的方式，speech token 就自带了每个字读出来的长度了。对于不经 speech token直接 text => mel谱的方法，就需要方式来决定每个text token 应该读多长时间了。

一种方式是有专门 model 或 model 的组件来预测每一个 token或音素的时长。 seed-tts 的方法是，只给一个 tts 结果总时长 T。由 model 来决定时间 T 内怎么把待念的 tokens 布局。时长 T 怎么给到 diffusion model？用 T 来决定出 input_noise.shape 的方式决定出： input_noise = [bs, seq_len=T, 80=mel谱维度]。

它支持语音编辑：

![image](https://github.com/user-attachments/assets/f5cf6b93-aff1-4dbe-bbf7-996b700c0a11)

### 两种方法的对比

![image](https://github.com/user-attachments/assets/bfd1549d-29b1-4b9b-8fdd-c1d204183726)

稳定性与相似度，都是 seed_TTS_DiT 占优。但是经 speech tokens 的版本，更适合流式推理、语音助手等低延迟场景（因为 DiT 只能一次性生成，而不能自回归逐步生成）。

---

## 参考：TorToise-tts： 2023.05 https://arxiv.org/pdf/2305.07243 《Better speech synthesis through scaling》

比它更早的 tortoise-TTS，无疑给了 seed-tts 很大的启发。tortroise-tts 就差不多是 `text ==(自回归)=> speech_tokens ==(扩散模型)=> mel谱 ==(vocoder)=> audio_wave` 模式的，除了没用 speech_tokens而是用了激活前的 latent。它的 speech tokens 的获取方式是：对 mel谱作 vqvae，从而得到 8192 个 audio tokens。

![image](https://github.com/user-attachments/assets/84d9e5df-da58-4caa-935e-f9eae642fe39)

CLVP（audio-text相关性model） 类似于 CLIP。生成多个用 CLVP 优选一个，是用的 delle的思路。如果忽略它，则是：

![image](https://github.com/user-attachments/assets/ad08995d-acd5-4487-ab10-f9355d17a31d)
