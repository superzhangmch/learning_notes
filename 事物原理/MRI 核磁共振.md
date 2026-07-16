对于一副图, 可以做2d Fourier 分解 ( https://github.com/superzhangmch/learning_notes/blob/main/%E6%95%B0%E5%AD%A6/%E5%82%85%E9%87%8C%E5%8F%B6%E7%BA%A7%E6%95%B0%E4%BD%9C%E7%94%BB.md ), 分解成 2d Base 的weighted sum. 只取前几项, 则就能大体看到图是啥样, 用的项越多, 还原越精细.

MRI 正是用了这样的原理. 一次 MRI, 会由多次的循环构成. 每个循环 step, 就是在测量 Fourier 某一分解项的系数. 

粗略说, 这个循环 step 里, 会对被测剖面施加一定的交变弱磁场(独立于磁场很强的主磁场), 这个弱磁场正好对应于 Fourier 的 base 项. 然后经过一定手段, 一次测量正好获得了对应的那个 Fourier 洗漱. 
