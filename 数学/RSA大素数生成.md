# RSA大素数生成

非对称加密的RSA算法的想法之牛逼就不说了。其基于的关键就是大整数分解之困难。

假如有一个500位长的大整数C，是由两个大素数A与B想撑得到的。如果要使得C最最不容易分解，那么可想而知，A与B的长度应该尽量接近250。如果有一天，这个500位长的整数也不安全了，那么当然就需要寻找下一个更大的整数，比如一个1000位长的，可以立马使得安全性提升n多。这时候为了获得这个1000位的大整数，那么自然的，就需要找到两个500位的大素数。

这样看一个大整数分解固然困难，但是找一个一半长度的素数又谈何容易：如果你觉得一个大数字是素数，那么检验这一点，岂不是已经是一个大工程了。

<br>

其实如果真是这样，那么RSA也就没法排上用场了。但是实际上，我们好多人，每天都是离不开这个东西的（比如https，ssh等等）。可见，这里面应该有什么奥秘。

<br>

实际上确实是。这个秘诀就是：其实很容易找到一个大素数！！而且几乎想要多大一个素数，可以立马生成一个。

<br>

那么，RSA所需要的大素数怎样生成的呢？简单说来是这样的：
1. 随机构造一个满足最终大素数长度的奇数
2. 判断这个奇数是不是素数。如果是，ok，结束；否则，加2，然后再检验，..., 再加2再检验，总会遇到一个素数的。

这里面有两个难点需要解决：
1. 怎样判断一个技术是素数？
2. 怎么保证不用太多次加2，就能保证获得一个素数？

下面分别说明。

1. 怎样判断一个技术是素数？  
   这有赖于一些方法，这些方法可以很容易的判断一个数字是不是素数。而且如果它判定是合数，那么并不能给出怎样分解来，只能指明可以分解而已。也就是说，判断一个数是合数容易，给出分解法难。  
   这些方法中，有一类是用的概率方式，以高概率来断定一个数是质数，可以把概率任意提高，但是不能保证一定是。比如miller-rabin算法。还有一些事肯定性判别的，但是往往比较慢。其中2002年几个印度人发明的 AKS 方式，则是给出了一个多项式可解的判别法！！  
   下面简述下miller-rabin算法。这个算法其实是一个循环“迭代”（非常规迭代，因为每轮之间是独立的）算法。“迭代”过程中，如果某步断定是一个合数【断定方式是：有某几个公式，质素一定成立，合数可能成立。所以只要不成立，那么一定是合数。而分明是合数，却成立的概率小于1/4】，那么一定是合数。否则，每一步都能以1/4概率的误判率断定是一个素数。如果需要更高的概率精度，那么就多做几轮【承上面括号中内容。如果一次误判的概率小于1/4, 那么没有理由做了n多次，每次都撞中了小概率】。这样概率可以任意提高。具体的该算法介绍，看wikipedia吧，再清楚不过：http://en.wikipedia.org/wiki/Miller–Rabin_primality_test 。本文只是介绍思路而已。
2. 怎么保证不用太多次加2，就能保证获得一个素数？  
  这个有赖于素数的概率分布情况。对于整数n，n处的连续两个素数的平均间隔大概是 ln(n), 而 ln(n)  往往很小了，所以从n开始不用做多少次(几百位的一个数，也就是只需要几十几百次而已)，就往往发现了一个素数了。而且因为这个平均间隔是比较小的，如果不是要找比n大最接近n的素数，那么这时候都可以在+2好多次（比如几万几十万）都没有找到一个素数的情况下，一下加一个较大的数字然后再次尝试。不可能每次总是需要+2好多好多次。

整体上就是这样。

下面是网上找的一个miller-rabin算法的python实现：
```
import random
_mrpt_num_trials = 5 # number of bases to test
def is_probable_prime(n):
   assert n > = 2
   # special case 2
   if n == 2:
       return True
   # ensure n is odd
   if n % 2 == 0:
       return False
   # write n-1 as 2**s * d
   # repeatedly try to divide n-1 by 2
   s = 0
   d = n-1
   while True:
       quotient, remainder = divmod(d, 2)
       if remainder == 1:
          break
       s += 1
       d = quotient
   assert(2**s * d == n-1)
 
   # test the base a to see whether it is a witness for the compositeness of n
   def try_composite(a):
       if pow(a, d, n) == 1:
          return False
       for i in range(s):
          if pow(a, 2**i * d, n) == n-1:
              return False
       return True # n is definitely composite
 
   for i in range(_mrpt_num_trials):
       a = random.randrange(2, n)
       if try_composite(a):
          return False
 
   return True # no base tested showed n as composite

def find_next_prime(n):
   if n %2 == 0:
       n += 1
   i = 0
   while False == is_probable_prime(n):
       n += 2
       i += 1
       if i > 50000:
          break;
          return 0
   print "loop used=%d, %d"%(i, i*2+2)
   return n

import sys
inn = sys.argv[1]
if False == is_probable_prime(int(inn)):
   print "not prime"
else:
   print "may be prime"
print find_next_prime(int(inn))
```
