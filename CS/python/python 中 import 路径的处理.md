# python 中 import 路径的处理

假如有个文件夹叫做aa, 下面有文件叫做bb.py, bb.py 中有类叫Cc。在使用到Cc的地方，会需要把 Cc import 进去，代码是：
```from aa.bb import Cc```

这时候往往会有问题是，找不到模块bb。
首先有可能是找不到aa，当然更找不到bb。因此需要在加载搜索路径中把aa所在的目录加进去。这个路径由 sys.path 指定。只需要把aa 所在的目录sys.path.append() 进去就可以了。
然后可能会发现还是找不到模块bb。这时候，需要在aa 目录下新建一个 __init__.py 文件。该文件内是可以写一些内容的。只是为了import Cc的话，可以为空。

如此这般，```from aa.bb import Cc``` 就会正常工作了。

但是还可能有个问题就是，如果多个python 各种复杂的互相错杂的import关系，会由于相对路径的一些问题导致总是不能正常 work。这时候有可能是由于sys.path.append() 的是相对路径，不是绝对路径。可以用 ```os.path.realpath(__file__)``` 获得绝对路径，然后就可以以绝对路径的形式 append了。

另外，如果希望不用sys.path.append(), 那么只需要export PYTHONPATH=... 环境变量。
