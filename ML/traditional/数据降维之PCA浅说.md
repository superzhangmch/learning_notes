# 数据降维之PCA浅说

PCA（rincipal Components Analysis ）是用于数据降维的。

PCA的所处理的原始数据，或者说输入数据，可以表示成一个矩阵：假设有 m 个样本点，每个样本点由n个特征组成，这样就是一个m*n 的矩阵。

PCA 降维，可以大概描述如下：
- 1). 对于原始数据先做一个平移使得每个维度上的平均值为0（也就是使得原点在数据的最中心）
- 2). 对于这个n维的特征空间，找到一个方向，使得数据在这个方向上有最大的方差（假如数据分布是个长长的椭圆形状，那么该方向就会是沿着长轴方向）
- 3). 然后在余下的n-1维与这个方向正交的子空间上重复找这样的方差最大话方向，一直重复下去。
- 4). 以上完成后可以看到，其实就是给原始数据找到了一个新的正交基，然后在新的基上表达原始数据而已。
- 5). 接下来按需要做降维：对每个n维向量的新基下的表示，截取其n个维度的前k个维度，作为这个向量的新的表示。这样原始的m*n矩阵变成了m*k矩阵。

之所以可以按以上(5)所说的那样通过截取来降维，是因为在以上所述的寻找新基的过程能保证，原始向量的新的基下的表示满足这样的特性：越在靠后的维度上，取值越小，从而可以忽略。

<br>

以上是说了PCA操作的思路。但是一个很重要的问题就是怎样找到那样的使得方差最大的方向向量。

关于这点，参看这里，思路就是列出最优化条件，然后发现居然可以用乘子法求这个的极值，好，那就求出来。假设上面转化（即平移使得远点居中）后的m*n矩阵是D, 神奇的是，这个方向居然是DTD的一个特殊特征值的特征向量。这个特殊特征值呢，正好是DTD的最大的特征值(注意DTD的所有特征值都非负)。关于这些，就看那篇文章。

上面只是求解的理论原理。实际上，PCA作为已经成熟的算法，当然已经总结出具体的操作步骤了。

简述如下：
1.  原始数据矩阵平移，使得原点居中，得到新矩阵
2.  求该新矩阵的协方差矩阵
3. 对协方差矩阵求特征值，特征向量
4. 截取前k大的特征值，以及对应特征向量
5. 得到原始数据去均值后的数据，在这些特征向量作为正交基所成空间下向量表示，从而得到降维的数据。

这里出现了个协方差矩阵。其实，这个协方差矩阵和上面的DTD基本上是一回事。DTD的每个元素都除以一某个常数(n或者n-1，取决于协方差矩阵怎么定义，有的用n有的用n-1)后，就是协方差矩阵。这个可以由协方差矩阵的定义（其计算也是先每个元素减去平均数）可知。

<br>

至于 PCA的应用，大概的说，就是直接应用降维后的数据，仿佛一开始就是这么少的维数。
示例代码如下：
```
def zeroMean(dataMat):
   meanVal=np.mean(dataMat,axis=0)
   newData=dataMat-meanVal
   return newData,meanVal

def pca(dataMat,n):
   newData,meanVal=zeroMean(dataMat)
   covMat=np.cov(newData,rowvar=0)

   eigVals,eigVects=np.linalg.eig(np.mat(covMat))
   eigValIndice=np.argsort(eigVals)
   n_eigValIndice=eigValIndice[-1:-(n+1):-1]
   n_eigVect=eigVects[:,n_eigValIndice]

   lowDDataMat=newData*n_eigVect

   reconMat=(lowDDataMat*n_eigVect.T)+meanVal
   return lowDDataMat,reconMat
mat = np.array([[3.,1.,4.,1.,5.], [1.,3.,5.,7.,9.], [0.,-1.,2., 0., 5.], [9.,1., 10., 5., -4.],]);
ret = pca(mat, 3)
print "-- original matrix --"
print mat
print "-- dimension-reduced matrix --"
print ret[0]
print "-- restored-matrix"
print ret[1]
```

output：
```
-- original matrix --
[[ 3.   1.  4.  1.  5.]
 [ 1.   3.  5.  7.  9.]
 [ 0.  -1.  2.  0.  5.]
 [ 9.   1. 10.   5. -4.]]
-- dimension-reduced matrix --
[[ 1.84332563  1.68607525  1.4174981 ]
 [ 4.6091374  -5.42641665  -0.2446524 ]
 [ 4.43657489  4.08674252 -0.93023591]
 [-10.88903792 -0.34640112  -0.24260979]]
-- restored-matrix
[[ 3.00000000e+00  1.00000000e+00  4.00000000e+00  1.00000000e+00 5.00000000e+00]
 [ 1.00000000e+00  3.00000000e+00  5.00000000e+00  7.00000000e+00  9.00000000e+00]
 [ 3.10862447e-15  -1.00000000e+00  2.00000000e+00 -4.44089210e-16 5.00000000e+00]
 [ 9.00000000e+00  1.00000000e+00  1.00000000e+01  5.00000000e+00  -4.00000000e+00]]
```
代码来自：http://blog.csdn.net/u012162613/article/details/42177327

参考：
- http://pinkyjie.com/2010/08/31/covariance/
- http://pinkyjie.com/2011/02/24/covariance-pca/
- http://www.cnblogs.com/LeftNotEasy/archive/2011/01/08/lda-and-pca-machine-learning.html
- 还有：《A tutorial on Principal Components Analysis》
