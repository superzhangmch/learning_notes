# 生图模型怎么做到把文字绘制到图上的

现在的文生图大模型都支持直接把文字绘到图里了。怎么做到的呢？

## Dall-e 3
[Dall-e3](https://cdn.openai.com/papers/dall-e-3.pdf) 的做法是：

> **5.2 Text rendering**
> 
>When building our captioner, we paid special attention to ensuring that it was able to **include prominent words
found in images in the captions** it generated. As a result, DALL-E 3 can generate text when prompted. During
testing, we have noticed that this capability is unreliable as words are have missing or extra characters. We
suspect this may have to do with the T5 text encoder we used: when the model encounters text in a prompt, it
actually sees tokens that represent whole words and must map those to letters in an image. In future work, we
would like to explore conditioning on character-level language models to help improve this behavior.

也就是说，通过在训练的时候，prompt 体现出要绘制"某某"文本的方式，让 model 自然学会的。训练集中的prompt告诉了image中有什么文字，从而model学会了绘制出相应的文字。
当然，因为被绘制的文本是 work level token，所以其文中说，char level 的应该会效果更好。

## SD 3.0
[SD 3.0](https://arxiv.org/pdf/2403.03206) 没提做了什么，就说有 typography / text 绘制能力了。因此想来也是和 dall-e3 一样靠数据集解决的问题。
另外它提到 DPO-finetuned 方法，也有帮助（原话是results in more aesthetically pleasing samples with better spelling），但只是锦上添花而已。
