# python eval 远比 json.loads 慢

一句话，对于一个 python dict 字符串，如果要解为 python dict，eval(...)的效率远比 json.loads 慢。

python dict 字符串内的引号可以是单引号也可以是双引号。eval 都接受。json.loads 只接受双引号，且返回的是 unicode 的 dict，看似 json.loads 用起来很不方便。但是即使加上编码转化时间，仍然是 json.loads 胜出。

至于原因，没深究。
