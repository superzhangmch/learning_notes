当前的 audio LM，生成语音最后都是 speech tokens id list => mel谱 => audio wave。而在 zhihu 文章 https://www.zhihu.com/question/793458414 中：可以根据一张频谱图照片还原出语音。

也就是说，只是根据 mel 谱，就差不多可以还原语音的。作语音合成也正是这么做的。

----

原始语音波形，可以提取频谱图【即 Spectrogram：对音频切成交叉的片段，每个片段作SFFT，从而得到该时间段的不同频率的振幅，然后画在一张图里，x坐标是时间，对应不同的片段，y坐标是频率，x-y坐标交叉点取不同颜色代表不同的振幅。也叫“语谱图”】。Mel谱，则是对频率做了非线性变换，使得更关注人耳敏感的频段。

所以从频谱图（或者Mel谱图），都是可以比较好地还原出语音的。从频谱图没有包含每个时间片段的波形的“相位”信息【相位指的是：对于正弦sine曲线，那么x=0对应sine的哪个位置？】，需要把相位找回来，然后才能还原。还原相位的一个比较简单而经典的方法是 Griffin-Lim 算法，此外还有神经网络的方法。

audio算法中的，vocoder（声码器）一般就是指的从频谱图或mel谱图还原声音的decoder。不少 tts 算法就是先由文字生成频谱图/mel谱图，再由 vocoder 解出声音。


而 MFCC 对声音的表示的压缩更严重（每个时间片段，只压缩到固定的12维向量来表示了），所以还原语音更困难。
librosa 中如 librosa.feature.inverse.mfcc_to_audio 等函数，既可以从这些特征表示逆向得到语音（虽然效果可能不咋样）。

----

小实验：

对于一段音频用 kimi-audio 的 audio_tokenizer 作tokenize, 然后经它的 flow-matching model 获得 mel谱后：对于 mel => wave 的转化代码，截获 mel 谱，并用 griffin-Lim 直接解：
```
      # kimi-audio: ./kimia_infer/models/detokenizer/__init__.py
      ...
      def ttt(mel_tensor):
            import numpy as np
            import librosa
            import librosa.feature
            import librosa.display
            import soundfile as sf
            mel = mel_tensor.to(torch.float32).cpu().numpy().T
            mel = np.exp(mel)
            sr = 22050           # 采样率
            n_fft = 1024         # FFT窗口大小
            hop_length = 512     # 帧移，建议保持一致
            win_length = 1024    # 窗口长度
            n_mels = 80          # Mel维度，与你的输入一致
            mel_basis = librosa.filters.mel(sr=sr, n_fft=n_fft, n_mels=n_mels)
            inv_mel_basis = np.linalg.pinv(mel_basis)
            S = np.dot(inv_mel_basis, mel)  # shape: [n_fft//2+1, time]
            audio = librosa.griffinlim(S, n_iter=60, hop_length=hop_length, win_length=win_length)
            sf.write('tmp/reconstructed.wav', audio, sr)


        if self.pre_mel is None:  # first chunk, related to TTFB
            ...
        else:
            concat_mel = torch.cat([self.pre_mel, speech_mel], dim=0) # shape = [seq_len, 80]
            ttt(concat_mel) # 截获，并生成音频 
            concat_reconstructed_wav = self.vocoder.decode_mel(concat_mel) # vocoder 生成音频
            ...
```
griffinlim 的音质差很多（有毛刺，不光滑），但是能听出是什么: 两个 audio 见： ./reconstructed_griffinlim.wav,  ./audio_file/reconstructed_vocoder.wav。


