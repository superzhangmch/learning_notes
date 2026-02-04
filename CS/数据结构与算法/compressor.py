"""
优化版 LZ77 + Huffman 压缩/解压工具

优化点:
1. 距离/长度分组编码 - 减少符号种类
2. 二进制格式存储编码表 - 替代 JSON
3. 规范 Huffman 编码 - 只存编码长度

用法:
    压缩: python compressor.py -c input.txt output.lzh
    解压: python compressor.py -d output.lzh restored.txt

AI 给出. 我加了些学习的注释.

"""

import sys
import struct
from collections import Counter
import heapq


# ==================== 距离/长度码表 ====================

# LZ77 找到重复后, 用(长度, 距离)表示重复的位置. 要对这个位置信息压缩表示
# 乃参考 DEFLATE 规范，简化版

# 长度码: (逐个增一的码值, 最小长度=min_len, 额外位数). 对于实际长度, 根据最小长度一列来决定选用哪个码值(idx), 一个码值可能代表多个长度, 所以要有额外位数来区分码值内的具体长度. 比如: (18, 51, 3), (19, 59, 3), 59-51=8=2**3, 所以需要额外的3bits
LENGTH_CODES = [
    (0, 3, 0), (1, 4, 0), (2, 5, 0), (3, 6, 0), (4, 7, 0),
    (5, 8, 0), (6, 9, 0), (7, 10, 0), (8, 11, 1), (9, 13, 1),
    (10, 15, 1), (11, 17, 1), (12, 19, 2), (13, 23, 2), (14, 27, 2),
    (15, 31, 2), (16, 35, 3), (17, 43, 3), (18, 51, 3), (19, 59, 3),
    (20, 67, 4), (21, 83, 4), (22, 99, 4), (23, 115, 4), (24, 131, 5),
    (25, 163, 5), (26, 195, 5), (27, 227, 5), (28, 258, 0),
]

# 距离码: (码值, 最小距离, 额外位数). 背后道理同 LENGTH_CODES.
DISTANCE_CODES = [
    (0, 1, 0), (1, 2, 0), (2, 3, 0), (3, 4, 0), (4, 5, 1), (5, 7, 1),
    (6, 9, 2), (7, 13, 2), (8, 17, 3), (9, 25, 3), (10, 33, 4), (11, 49, 4),
    (12, 65, 5), (13, 97, 5), (14, 129, 6), (15, 193, 6), (16, 257, 7),
    (17, 385, 7), (18, 513, 8), (19, 769, 8), (20, 1025, 9), (21, 1537, 9),
    (22, 2049, 10), (23, 3073, 10), (24, 4097, 11), (25, 6145, 11),
    (26, 8193, 12), (27, 12289, 12), (28, 16385, 13), (29, 24577, 13),
]


def encode_length(length: int) -> tuple[int, int, int]:
    """长度 -> (码值, 额外位数, 额外值)"""
    for i in range(len(LENGTH_CODES) - 1, -1, -1):
        code, base, extra_bits = LENGTH_CODES[i]
        if length >= base:
            extra_val = length - base
            return code, extra_bits, extra_val
    return 0, 0, 0


def decode_length(code: int, extra_val: int) -> int:
    """(码值, 额外值) -> 长度"""
    _, base, _ = LENGTH_CODES[code]
    return base + extra_val


def encode_distance(distance: int) -> tuple[int, int, int]:
    """距离 -> (码值, 额外位数, 额外值)"""
    for i in range(len(DISTANCE_CODES) - 1, -1, -1):
        code, base, extra_bits = DISTANCE_CODES[i]
        if distance >= base:
            extra_val = distance - base
            return code, extra_bits, extra_val
    return 0, 0, 0


def decode_distance(code: int, extra_val: int) -> int:
    """(码值, 额外值) -> 距离"""
    _, base, _ = DISTANCE_CODES[code]
    return base + extra_val


# ==================== LZ77 部分 ====================

def lz77_compress_v2(data: bytes, window_size: int = 32768, max_length: int = 258) -> list:
    """LZ77 压缩 - 哈希表优化版"""
    result = []
    i = 0
    n = len(data)

    # 哈希表: 3字节哈希 -> 最近位置（只保留一个，链式查找）
    # 使用 head + prev 链表结构，类似 gzip
    head = {}  # hash -> 最近的位置
    prev = [0] * min(n, window_size)  # prev[pos % window_size] -> 前一个相同hash的位置

    def get_hash(pos):
        if pos + 3 > n:
            return None
        # 简单哈希
        return ((data[pos] << 16) | (data[pos+1] << 8) | data[pos+2]) & 0xFFFFFF

    def insert_hash(pos):
        h = get_hash(pos)
        if h is None:
            return
        idx = pos % window_size
        if h in head:
            prev[idx] = head[h]
        else:
            prev[idx] = 0
        head[h] = pos

    while i < n:
        best_distance = 0
        best_length = 0

        h = get_hash(i)

        if h is not None and h in head:
            # 沿链表查找，最多查 32 个候选
            j = head[h]
            chain_len = 0
            max_chain = 64

            while j > 0 and i - j <= window_size and chain_len < max_chain:
                # 快速检查：先比较前3字节
                if data[j] == data[i] and data[j+1] == data[i+1] and data[j+2] == data[i+2]:
                    # 计算完整匹配长度
                    length = 3
                    while (i + length < n and
                           length < max_length and
                           data[j + length] == data[i + length]):
                        length += 1

                    if length > best_length:
                        best_length = length
                        best_distance = i - j

                        # 找到足够长的匹配就停止
                        if best_length >= 128:
                            break

                # 沿链表向前
                chain_len += 1
                next_j = prev[j % window_size]
                if next_j >= j or next_j == 0:
                    break
                j = next_j

        if best_length >= 3:
            # 插入这段所有位置的哈希
            for k in range(i, min(i + best_length, n - 2)):
                insert_hash(k)

            len_code, len_extra_bits, len_extra_val = encode_length(best_length)
            dist_code, dist_extra_bits, dist_extra_val = encode_distance(best_distance)

            result.append(("L", len_code, len_extra_bits, len_extra_val))
            result.append(("D", dist_code, dist_extra_bits, dist_extra_val))
            i += best_length
        else:
            insert_hash(i)
            result.append(("B", data[i]))
            i += 1

    result.append(("E",))
    return result


def lz77_compress(data: bytes, window_size: int = 32768, max_length: int = 258) -> list:
    """LZ77 压缩，返回符号列表"""
    result = []
    i = 0

    while i < len(data):
        best_distance = 0
        best_length = 0

        search_start = max(0, i - window_size)

        # 上面的 v2, 不过是把下面的暴力遍历用 hash 来加速
        for j in range(search_start, i):
            length = 0
            while (i + length < len(data)        # 不超 text 末尾
                       and length < max_length   # 不超最大检测长度(258)
                       and data[j + (length % (i - j))] == data[i + length]): # 如果持续匹配(说明找到了重复)
               	length += 1

            if length > best_length: # 从最近的 window_size 内, 找到最大重复
                best_length = length
                best_distance = i - j

        if best_length >= 3:
            # 引用: 用特殊标记 256-285 表示长度码
            len_code, len_extra_bits, len_extra_val = encode_length(best_length)
            dist_code, dist_extra_bits, dist_extra_val = encode_distance(best_distance)

            # 记录下重复位置的 location & distance
            result.append(("L", len_code, len_extra_bits, len_extra_val))
            result.append(("D", dist_code, dist_extra_bits, dist_extra_val))
            # 既然找到了重复, 就把位置往后推进
            i += best_length
        else:
            # 没找到重复, 则直接输出原始字节: 0-255
            result.append(("B", data[i]))
            i += 1

    # 结束标记
    result.append(("E",))

    if 0:
        for x in result: 
            if x[0] == 'B':
                print ('===', x[0], x[1], "|%s|" % chr(x[1]))
            else:
                print ('===', x)
    return result


def lz77_decompress(symbols: list) -> bytes:
    """LZ77 解压"""
    result = bytearray()
    i = 0

    while i < len(symbols):
        sym = symbols[i]

        if sym[0] == "B":
            result.append(sym[1])
            i += 1
        elif sym[0] == "L":
            _, len_code, _, len_extra = sym
            length = decode_length(len_code, len_extra)

            i += 1
            _, dist_code, _, dist_extra = symbols[i]
            distance = decode_distance(dist_code, dist_extra)

            start = len(result) - distance
            for j in range(length):
                result.append(result[start + (j % distance)])
            i += 1
        elif sym[0] == "E":
            break
        else:
            i += 1

    return bytes(result)


# ==================== Huffman 部分 ====================

class HuffmanNode:
    def __init__(self, sym=None, freq=0, left=None, right=None):
        self.sym = sym
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(freq_map: dict):
    if not freq_map:
        return None
    heap = [HuffmanNode(sym, freq) for sym, freq in freq_map.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0]


def get_code_lengths(node, depth=0, lengths=None):
    """获取每个符号的编码长度"""
    if lengths is None:
        lengths = {}

    if node is None:
        return lengths

    if node.sym is not None:
        lengths[node.sym] = max(depth, 1)
    else:
        get_code_lengths(node.left, depth + 1, lengths)
        get_code_lengths(node.right, depth + 1, lengths)

    return lengths


def build_canonical_codes(lengths: dict) -> dict:
    """从编码长度构建规范 Huffman 编码"""
    if not lengths:
        return {}

    # 按长度和符号排序
    sorted_syms = sorted(lengths.keys(), key=lambda s: (lengths[s], s))

    codes = {}
    code = 0
    prev_len = 0

    for sym in sorted_syms:
        curr_len = lengths[sym]
        code <<= (curr_len - prev_len)
        codes[sym] = format(code, f'0{curr_len}b')
        code += 1
        prev_len = curr_len

    return codes


# ==================== 位流处理 ====================

class BitWriter:
    def __init__(self):
        self.data = bytearray()
        self.buffer = 0
        self.bits_in_buffer = 0

    def write_bits(self, value: int, num_bits: int):
        """写入指定位数"""
        for i in range(num_bits - 1, -1, -1):
            bit = (value >> i) & 1
            self.buffer = (self.buffer << 1) | bit
            self.bits_in_buffer += 1
            if self.bits_in_buffer == 8:
                self.data.append(self.buffer)
                self.buffer = 0
                self.bits_in_buffer = 0

    def write_code(self, code: str):
        """写入 Huffman 编码"""
        for bit in code:
            self.buffer = (self.buffer << 1) | int(bit)
            self.bits_in_buffer += 1
            if self.bits_in_buffer == 8:
                self.data.append(self.buffer)
                self.buffer = 0
                self.bits_in_buffer = 0

    def flush(self) -> tuple[bytes, int]:
        """返回 (数据, padding位数)"""
        padding = 0
        if self.bits_in_buffer > 0:
            padding = 8 - self.bits_in_buffer
            self.buffer <<= padding
            self.data.append(self.buffer)
        return bytes(self.data), padding


class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.bit_pos = 0

    def read_bits(self, num_bits: int) -> int:
        """读取指定位数"""
        result = 0
        for _ in range(num_bits):
            if self.pos >= len(self.data):
                return result
            bit = (self.data[self.pos] >> (7 - self.bit_pos)) & 1
            result = (result << 1) | bit
            self.bit_pos += 1
            if self.bit_pos == 8:
                self.bit_pos = 0
                self.pos += 1
        return result

    def read_huffman(self, decode_map: dict):
        """读取一个 Huffman 编码的符号"""
        code = ""
        while code not in decode_map:
            if self.pos >= len(self.data):
                return None
            bit = (self.data[self.pos] >> (7 - self.bit_pos)) & 1
            code += str(bit)
            self.bit_pos += 1
            if self.bit_pos == 8:
                self.bit_pos = 0
                self.pos += 1
        return decode_map[code]


# ==================== 编码表序列化 ====================

# 符号类型: B=字节(0-255), L=长度码(256-284), D=距离码(285-314), E=结束(315)
SYM_BYTE_BASE = 0
SYM_LEN_BASE = 256
SYM_DIST_BASE = 285
SYM_END = 315
TOTAL_SYMBOLS = 316


def sym_to_int(sym) -> int:
    """符号 -> 整数"""
    if sym[0] == "B":
        return SYM_BYTE_BASE + sym[1]
    elif sym[0] == "L":
        return SYM_LEN_BASE + sym[1]
    elif sym[0] == "D":
        return SYM_DIST_BASE + sym[1]
    elif sym[0] == "E":
        return SYM_END
    return 0


def int_to_sym_type(val: int) -> str:
    """整数 -> 符号类型"""
    if val < SYM_LEN_BASE:
        return "B"
    elif val < SYM_DIST_BASE:
        return "L"
    elif val < SYM_END:
        return "D"
    else:
        return "E"


def serialize_code_lengths(lengths: dict) -> bytes:
    """
    序列化编码长度表
    格式: 316 个 4-bit 值 (每个符号的编码长度, 0表示不存在)
    """
    result = bytearray()
    values = [lengths.get(i, 0) for i in range(TOTAL_SYMBOLS)]

    for i in range(0, TOTAL_SYMBOLS, 2):
        v1 = min(values[i], 15)
        v2 = min(values[i + 1] if i + 1 < TOTAL_SYMBOLS else 0, 15)
        result.append((v1 << 4) | v2)

    return bytes(result)


def deserialize_code_lengths(data: bytes) -> dict:
    """反序列化编码长度表"""
    lengths = {}
    for i, byte in enumerate(data):
        v1 = (byte >> 4) & 0xF
        v2 = byte & 0xF

        idx1 = i * 2
        idx2 = i * 2 + 1

        if v1 > 0 and idx1 < TOTAL_SYMBOLS:
            lengths[idx1] = v1
        if v2 > 0 and idx2 < TOTAL_SYMBOLS:
            lengths[idx2] = v2

    return lengths


# ==================== 压缩/解压 ====================

def compress_data(data: bytes, verbose: bool = False, use_v2: bool = True) -> bytes:
    """压缩数据"""
    if len(data) == 0:
        return struct.pack(">I", 0)

    original_size = len(data)

    # LZ77 压缩
    if use_v2:
        lz77_result = lz77_compress_v2(data)
    else:
        lz77_result = lz77_compress(data)

    # 统计 LZ77 结果
    literal_count = sum(1 for s in lz77_result if s[0] == "B")
    ref_count = sum(1 for s in lz77_result if s[0] == "L")

    # 转为整数符号
    int_symbols = []
    total_extra_bits = 0

    for sym in lz77_result:
        int_sym = sym_to_int(sym)
        int_symbols.append(int_sym)

        if sym[0] in ("L", "D"):
            _, code, extra_bits, extra_val = sym
            total_extra_bits += extra_bits

    # LZ77 后的理论大小（固定编码：字节8位，长度码5位，距离码5位）
    lz77_fixed_bits = literal_count * 8 + ref_count * 2 * 5 + total_extra_bits
    lz77_fixed_bytes = (lz77_fixed_bits + 7) // 8

    # 构建 Huffman 编码
    freq_map = Counter(int_symbols)
    tree = build_huffman_tree(freq_map)
    lengths = get_code_lengths(tree)
    codes = build_canonical_codes(lengths)

    # 计算 Huffman 编码后的位数
    huffman_bits = sum(len(codes[sym_to_int(sym)]) for sym in lz77_result)
    huffman_bits += total_extra_bits  # 额外位还是要的
    huffman_bytes = (huffman_bits + 7) // 8

    # 写入压缩数据
    writer = BitWriter()

    for sym in lz77_result:
        int_sym = sym_to_int(sym)
        writer.write_code(codes[int_sym])

        if sym[0] in ("L", "D"):
            _, code, extra_bits, extra_val = sym
            if extra_bits > 0:
                writer.write_bits(extra_val, extra_bits)

    compressed_bits, padding = writer.flush()

    # 序列化编码长度表
    lengths_data = serialize_code_lengths(lengths)

    # 打印详情
    if verbose:
        print(f"\n  [压缩详情]")
        print(f"  原始大小: {original_size} 字节")
        print(f"  ─────────────────────────────────")
        print(f"  LZ77: {literal_count} 原始字节 + {ref_count} 引用")
        print(f"  LZ77 后 (固定编码): {lz77_fixed_bytes} 字节 ({lz77_fixed_bytes/original_size*100:.1f}%)")
        print(f"  ─────────────────────────────────")
        print(f"  Huffman 后 (数据部分): {huffman_bytes} 字节 ({huffman_bytes/original_size*100:.1f}%)")
        print(f"  + 编码表: {len(lengths_data)} 字节")
        print(f"  + 头部: 5 字节")
        print(f"  ─────────────────────────────────")
        print(f"  最终大小: {5 + len(lengths_data) + len(compressed_bits)} 字节 ({(5 + len(lengths_data) + len(compressed_bits))/original_size*100:.1f}%)")

    # 文件格式:
    # [4字节: 原始长度] [1字节: padding] [158字节: 编码长度表] [压缩数据]
    header = struct.pack(">I", len(data))
    header += struct.pack("B", padding)

    return header + lengths_data + compressed_bits


def decompress_data(compressed: bytes) -> bytes:
    """解压数据"""
    if len(compressed) < 5:
        raise ValueError("无效的压缩文件")

    # 读取头部
    original_length = struct.unpack(">I", compressed[0:4])[0]
    if original_length == 0:
        return b""

    padding = compressed[4]

    # 读取编码长度表
    lengths_data = compressed[5:5 + (TOTAL_SYMBOLS + 1) // 2]
    lengths = deserialize_code_lengths(lengths_data)

    # 重建 Huffman 编码
    codes = build_canonical_codes(lengths)
    decode_map = {v: k for k, v in codes.items()}

    # 读取压缩数据
    compressed_data = compressed[5 + (TOTAL_SYMBOLS + 1) // 2:]

    # 移除 padding
    if padding > 0 and len(compressed_data) > 0:
        # 保持原样，读取时会自然停止
        pass

    reader = BitReader(compressed_data)

    # 解码
    symbols = []
    while True:
        int_sym = reader.read_huffman(decode_map)
        if int_sym is None:
            break

        sym_type = int_to_sym_type(int_sym)

        if sym_type == "B":
            symbols.append(("B", int_sym - SYM_BYTE_BASE))
        elif sym_type == "L":
            len_code = int_sym - SYM_LEN_BASE
            _, _, extra_bits = LENGTH_CODES[len_code]
            extra_val = reader.read_bits(extra_bits) if extra_bits > 0 else 0
            symbols.append(("L", len_code, extra_bits, extra_val))
        elif sym_type == "D":
            dist_code = int_sym - SYM_DIST_BASE
            _, _, extra_bits = DISTANCE_CODES[dist_code]
            extra_val = reader.read_bits(extra_bits) if extra_bits > 0 else 0
            symbols.append(("D", dist_code, extra_bits, extra_val))
        elif sym_type == "E":
            symbols.append(("E",))
            break

    # LZ77 解压
    return lz77_decompress(symbols)


# ==================== 文件操作 ====================

def compress_file(input_path: str, output_path: str):
    """压缩文件"""
    print(f"读取文件: {input_path}")
    with open(input_path, "rb") as f:
        data = f.read()

    original_size = len(data)
    print(f"原始大小: {original_size:,} 字节")

    print("压缩中...")
    compressed = compress_data(data, verbose=True)
    compressed_size = len(compressed)

    with open(output_path, "wb") as f:
        f.write(compressed)

    ratio = compressed_size / original_size * 100 if original_size > 0 else 0
    saved = original_size - compressed_size
    print(f"压缩后大小: {compressed_size:,} 字节")
    print(f"压缩率: {ratio:.1f}% (节省 {saved:,} 字节)")
    print(f"已保存到: {output_path}")


def decompress_file(input_path: str, output_path: str):
    """解压文件"""
    print(f"读取压缩文件: {input_path}")
    with open(input_path, "rb") as f:
        compressed = f.read()

    print(f"压缩文件大小: {len(compressed):,} 字节")

    print("解压中...")
    data = decompress_data(compressed)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"解压后大小: {len(data):,} 字节")
    print(f"已保存到: {output_path}")


def print_usage():
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=" * 50)
        print("优化版压缩演示")
        print("=" * 50)

        # 测试
        test_cases = [
            ("重复文本", b"Hello World! " * 100),
            ("代码片段", b'''def hello(): print("Hello World!") def main(): for i in range(100): hello() print(f"Count: {i}") if __name__ == "__main__": main() ''' * 20), ]

        for name, data in test_cases:
            print(f"\n{'='*50}")
            print(f"[{name}]")

            compressed = compress_data(data, verbose=True)

            restored = decompress_data(compressed)
            print(f"  验证: {'✓ 成功' if restored == data else '✗ 失败'}")

        print("\n" + "=" * 50)
        print_usage()

    elif len(sys.argv) != 4:
        print_usage()
        sys.exit(1)
    else:
        mode = sys.argv[1]
        input_path = sys.argv[2]
        output_path = sys.argv[3]

        if mode == "-c":
            compress_file(input_path, output_path)
        elif mode == "-d":
            decompress_file(input_path, output_path)
        else:
            print(f"未知选项: {mode}")
            print_usage()
            sys.exit(1)
