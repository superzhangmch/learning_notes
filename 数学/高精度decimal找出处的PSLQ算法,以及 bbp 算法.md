对一个根据某种表达式算出的高精度decimal, 如何找到这个原始表达式, 是 PSLQ 算法能做的事. 

而 BBP 公式, 正式用它发现的. (BBP 公式可拆解成8个级数, 提前把8个 series 的前 n 项和算出(保证精度足够), 然后用 PSLQ 来拟合系数, 就得到了 BBP 公式). 现在大规模算 pi, 都是binary 上算, 然后用 bbp 跳步检查尾数正确性(bin <=> hex 是零成本的), 没问题再把 binary => decimal. 

