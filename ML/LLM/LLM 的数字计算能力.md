# LLM 的数字计算能力

如果让 LLM 直接给出一个四则计算的答案，一般表现都不怎样。

### 1. 如果是简单的多个数字求和，则表现得较好：

太简单的不论。这里列一个有点难度的：

```
(one hundred and thirty one) plus (257 plus 24)+35+12+(thirteen plus 2557)=?, show me the answer directly, no details
```

- claude 3.5:  3029. 正确 
- gpt 4o: 3028. 差1.
- gpt 4: 3069 （如果全换成数字，则无压力得出：3029）

### 2. 如果是复杂式子： 131+257*24+35+12+13*2557=39587

试了多家，发现发现也就 gemini 可以。

甚至难度再进一步，也只 gemini 答对了：
```
(one hundred and thirty one) plus (257 times 24)+35+12+(thirteen times 2557)=?, show me the answer directly, no details (however, you should output using english not Arabic numbers)
```
- gemini 1.5 flash: 39587
- gemini 2.0 flash: thirty-nine thousand five hundred and eighty-seven. 正确
- claude3.5 sonet:  thirty three thousand eight hundred and twenty eight （不对）
- GPT4: Sixty four thousand four hundred and fifty six（胡说）

我猜测是 gemini 加了计算外挂. 后来测试：```what's the weather today in New York?```, 返回的答案是真实的，因此说明确实是走了计算外挂。

### 其他

然而，从一系列数字的加法上看，如果不是特别复杂的数字（5480+8167+8927+5541+3653+5567+8768+3381+4302+8709这样的就挂了），LLM 是能直接得到正确答案的。多个数字加，需要处理好进位等问题。 LLM 怎么做到的？

