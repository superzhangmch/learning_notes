# 根据音乐生成舞蹈（music2dance）怎么做的

特考察 2022：《EDGE：editable dance generation from music》，2024：《POPDG：popular 3D dance generation from PopDanceSet》、2024：《lodge: a coarse to fine diffusion network for long dance generation guided by the characteristic dance primitives》三文。以便管窥一下。

三者都是 diffusion model的。

### EDGE
----

**特征表示**：对于24个关节点，每个关节点按说用xyz三个坐标点的时间序列表示即可，但是一般会用相对变化来表示：假设肢体长度不变，则只需描述肢体相对关节的转动角度即可。比如说前臂绕肘的变化，用xyz三个方向的角度变化来描述即可。但是直接用角度会导致本来连续的肢体动作，在特征空间变得不连续：0度和360度，其实是一样的，但是变化却是360. 为了解决这个问题，要用一个 3x3 的正交矩阵来表示 3d 空间的转动。而只需6个变量就可以决定一个3x3正交矩阵的所有取值。

这样，每个关节点其实需要用6个数字来表示。24个关节需要 24 x 6 = 144 维向量来表示。除此外，还需要一个3维向量来表示人体在空间的移动，对于脚尖脚跟还各需要两个特征表示是否着地，左右脚共4个。这样一共需要144+3+4=151维表示一帧。

**diffusion input/output**: music audio 参与 cross attention，自不待言。diffusion 每个 step $x_t \rightarrow x_{t-1}$ 时， $x_t的shape = [batch\_size, 总帧数, 151维的pose特征]$，总帧数是5秒每秒30帧，共150帧，也就是一次生成5秒舞蹈。对于 x_0, 会把151维的每一个维度 shift + rescale 弄成 [-1, 1] 的取值范围内，除此外没其他变换，直接让给diffusion model。

**model 与 loss**：

注意一点是，loss 不止用 diffusion loss。

![image](https://github.com/user-attachments/assets/6cf41606-f271-485f-bbbc-43dac854fbc2)

**editable 与 长舞蹈生成**：作为diffusion的model，有如图片diffusion，编辑功能以及只跟一半补全其余的功能自然不在话下。超过5秒的长dance生成，靠的前后两个5s片段重叠2.5秒的方式，有如图片的outpainting外扩生成。

其他两种方法本质上差不多，不详述。

### LODGE

两步法生成长舞蹈。第一步生成30s的长舞蹈的音乐节拍点处的pose（即先生成梗概)，第二步根据节拍点处的key pose填充细节。

### POPDG
3d 人体关节点数据，用3d关节点识别算法从舞蹈视频识别出。EDGE 的3d关节点舞蹈数据是从多视角的多个视频经算法作三维重构而得到的，很麻烦。该文证实不必如此麻烦。

### 其他

另外还有一个 基于 transformer 的 UniMuMo 方法。它把music 与舞蹈pose序列都经过自编码器token化，如同训LLM训一个transformer。生成时用 music token list 当做 prompt，然后让 model 续写出 dance token list，再解出舞蹈。它的数据集靠把任意音乐的节拍点序列与任意舞蹈的（一定算法识别出的）关节pose序列，作强行的伸缩插值对齐，从而构造出。
