import itertools

'''
1~19不重复填充后，横竖斜和都是38：
     (16, 19, 3)
    (12, 2, 7, 17)
  (10, 4, 5, 1, 18)
   (13, 8, 6, 11)
    (15, 14, 9)
遍历解决之。
'''

t = sum([i for i in range(1, 19+1)])
avg = t / 5.
assert avg == 38
SUM = avg

def find(arr, last_i, arr_len, total):
    # Find all the subarrays with a length equal to arr_len and a sum equal to total
    if arr_len <= 0:
        return None
    total_arr = []
    for i in range(len(arr)):
        a = arr[i]
        #print (a, arr_len, total)
        if a <= last_i: continue

        if a == total and arr_len == 1:
            total_arr.append([a])
        else:
            out = find(arr, a, arr_len-1, total-a)
            if out:
                for o in out:
                    total_arr.append([a] + o)
                    #print (out, arr_len, 'v', total_arr)
    if not total_arr:
        return None
    return total_arr

arr = [i for i in range(1, 19+1)]
out3 = find(arr, last_i=0, arr_len=3, total=SUM)
out4 = find(arr, last_i=0, arr_len=4, total=SUM)
out5 = find(arr, last_i=0, arr_len=5, total=SUM)

out3 = [set(o) for o in out3] # 含3个元素且和为SUM的所有数组
out4 = [set(o) for o in out4] # 含4个
out5 = [set(o) for o in out5] # 含5个

for o in out3: assert sum(o) == SUM
for o in out4: assert sum(o) == SUM
for o in out5: assert sum(o) == SUM
print (len(out3), len(out4), len(out5))

def check_if_ok(a30, a40, a5, a41, a31):
    # 分别按 a30, a40, a5, a41, a31 排成六行，构成六边形。检查各条边的和是否为 SUM
    s = a30[0] + a40[0] + a5[0]
    if s != SUM: return False
    s = a30[-1] + a40[-1] + a5[-1]
    if s != SUM: return False

    s = a31[0] + a41[0] + a5[0]
    if s != SUM: return False
    s = a31[-1] + a41[-1] + a5[-1]
    if s != SUM: return False
    # --

    s = a30[1] + a40[1] + a5[1] + a41[0]
    if s != SUM: return False
    s = a30[-2] + a40[-2] + a5[-2] + a41[-1]
    if s != SUM: return False

    s = a40[0] + a5[1] + a41[1] + a31[1]
    if s != SUM: return False
    s = a40[-1] + a5[-2] + a41[-2] + a31[-2]
    if s != SUM: return False

    s = a30[2] + a40[2] + a5[2] + a41[1] + a31[0]
    if s != SUM: return False

    s = a30[0] + a40[1] + a5[2] + a41[2] + a31[2]
    if s != SUM: return False
    return True

def check(o30, o40, o5, o41, o31):
    # 分别按 o30, o40, o5, o41, o31 排成六行，构成六边形。检查各条边的和是否为 SUM
    # o30, o40, o5, o41, o31 分别有 3, 4, 5, 4, 3 个元素
    # 对 o30, o40, o5, o41, o31 中每个数组要作排列组合，以便遍历之
    def all_comb(arr):
        return itertools.permutations(arr)
    
    for a5 in all_comb(o5):
        arr1 = []
        for a30 in all_comb(o30):
            for a40 in all_comb(o40):
                s = a30[0] + a40[0] + a5[0]
                if s != SUM: continue
                s = a30[-1] + a40[-1] + a5[-1]
                if s != SUM: continue
                arr1.append([a30, a40])
        if not arr1: continue
        arr2 = []
        for a31 in all_comb(o31):
            for a41 in all_comb(o41):
                s = a31[0] + a41[0] + a5[0]
                if s != SUM: continue
                s = a31[-1] + a41[-1] + a5[-1]
                if s != SUM: continue
                arr2.append([a31, a41])
        if not arr2: continue
        for a30, a40 in arr1:
            for a31, a41 in arr2:
                r = check_if_ok(a30, a40, a5, a41, a31)
                if r: return [a30, a40, a5, a41, a31]
    return False

# 遍历
c = 0
for o5 in out5:
    for o30 in out3:
        if (o5 & o30): continue
        for o31 in out3:
            if (o5  & o31): continue
            if (o30 & o31): continue
            for o40 in out4:
                if (o5  & o40): continue
                if (o30 & o40): continue
                if (o31 & o40): continue
                for o41 in out4:
                    if (o5  & o41): continue
                    if (o30 & o41): continue
                    if (o31 & o41): continue
                    if (o40 & o41): continue
                    c += 1
                    r = check(o30, o40, o5, o41, o31)
                    if r  or c % 500 == 0:
                        if not r:
                            print ('trying .. ', r, c)
                        else:
                            o_30, o_40, o_5, o_41, o_31 = r
                            print ("--- find ---")
                            print ("     ", o_30)
                            print ("   ", o_40)
                            print (" ", o_5)
                            print ("   ", o_41)
                            print ("     ", o_31)
                            print ("---")
