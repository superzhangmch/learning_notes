#出于需要，搞一小段，为了以后再用，备忘如下：
#---------------------------------------------------------------------------------------
import sys
import re
lines = open(sys.argv[1]).readlines() # 输入文件
fp_out = open(sys.argv[2], "w")       # 输出文件
tm_adjust = 4500                         #计划怎样调整。这里表示快进4.5秒，倒退则是负数

def do_tm_adjust(b, tm_adjust):
    tm_1 = 1000 * (b[0] * 3600 + b[1] * 60 + b[2] ) + b[3]
    tm_1 += tm_adjust
    b[3] = tm_1 % 1000; tm_1 = tm_1 / 1000
    b[2] = tm_1 % 60; tm_1 = tm_1 / 60
    b[1] = tm_1 % 60; tm_1 = tm_1 / 60
    b[0] = tm_1

for line in lines:
    a = re.search('^ *([0-9]+):([0-9]+):([0-9]+),([0-9]+)[ \t]*-->[ \t]*([0-9]+):([0-9]+):([0-9]+),([0-9]+) *$', line.strip())
    if not a:
       fp_out.write(line)
    else:
       # 00:00:54,000 --> 00:01:01,000
       b = [int(i) for i in a.groups()[0:4]]
       do_tm_adjust(b, tm_adjust)
       bb = [int(i) for i in a.groups()[4:8]]
       do_tm_adjust(bb, tm_adjust)

       fp_out.write("d:d:d,d --> d:d:d,d\n"%(b[0], b[1], b[2], b[3], bb[0], bb[1], bb[2], bb[3]))
fp_out.close()
