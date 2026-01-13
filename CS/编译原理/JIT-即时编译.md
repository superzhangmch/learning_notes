by chatgpt
 
## JIT 是什么？（一句话版）

> **JIT 的本质不是“编译”，
> 而是“带回退能力的投机执行”。**

它在运行时：

* 观察程序行为
* 对“高概率成立的情况”做激进优化
* 一旦假设失效，**安全回退（deopt）**，保证语义正确

重要: 
- JIT 的“安全回退（deopt）”是在“已经生成并正在执行的机器码（binary code）内部触发的”，但回退的“落点”通常不是继续执行这段机器码，而是跳回解释器 / baseline code。
- 从 JIT 生成的 binary code 回退（deopt）之后，程序的“可观察语义效果”会 仿佛它一直是通过解释执行走到这里的一样。

### JIT 的标准整体结构

```text
解释执行
  ↓
热点探测（profiling）
  ↓
基于假设的编译（speculative compilation）
  ↓
插入 guard
  ↓
执行优化代码
  ↓
guard 失败 → deopt → 回到解释器
```

### JIT 的“三件套”（核心心智模型）

> **Profile + Speculation + Deoptimization**

| 名称          | 含义              |
| ----------- | --------------- |
| Profile     | 运行时统计（类型、分支、调用） |
| Speculation | 基于统计做假设         |
| Deopt       | 假设失败时安全回退       |

**没有 deopt，就不可能有激进优化。**

---

## 回退: Guards（守卫）

Guard 在 binary code 里长什么样？

```asm
cmp [obj.map], expected_map
jne deopt_stub
```

这段 cmp / jne 就是编译进 binary code 的, deopt_stub 是预先生成的回退入口. 

<img width="676" height="328" alt="image" src="https://github.com/user-attachments/assets/f1507225-2163-4213-9190-e22af25a9cec" />

### “标志位”视角

> “看起来 jit 的根本在于有一些标志位，如果下一次循环标志位没变就用编译好的，否则回退”

这抓住了 JIT 的关键本质：

> **JIT 本质上依赖一组“状态是否仍成立”的标志位：
> 如果下次执行时这些标志没变 → 走优化路径；
> 否则 → 回退。**

在 JIT 术语中，这些“标志位”叫：

* **Guards（守卫）**
* **Assumptions（假设）**

### 常见的 Guard / 假设类型

| 假设内容   | Guard 示例             |
| ------ | -------------------- |
| 类型没变   | `if (x is int)`      |
| 对象结构没变 | hidden class / shape |
| 只有一个实现 | class hierarchy      |
| 分支稳定   | branch guard         |
| 没逃逸    | escape analysis      |
| 没竞争    | lock state           |

👉 **这些 guard 就是“标志位检查”**

### Deoptimization（回退）是什么？

> **把“优化后的机器码状态”
> 精确还原为“语言语义层的状态”**

包括：

* 栈帧
* 局部变量
* 操作数栈
* 程序计数位置

**Deopt 不是异常:**

* 是 **设计内机制**
* 正常、频繁、可预期

----

## JIT 的三种主流路线

### (1). Method-based JIT（Java / V8）

* 编译整个函数
* SSA / 图 IR
* 优化强
* Deopt 复杂

### (2). Trace-based JIT（PyPy / LuaJIT）

* 编译热点循环路径
* 假设分支稳定
* 对动态语言友好
* 分支多时效果差

### (3). 多层 JIT（现代主流）

```
解释器
  ↓
Baseline JIT
  ↓
Optimizing JIT
```

---

## 动态语言 vs 静态语言中的 JIT

### 动态语言（JS / Python）

* 类型不固定
* 大量 guard
* 频繁 deopt
* 工程复杂度极高

###  静态语言（Java / C# / WASM）

* 类型固定
  * 所以它做 Jit 就要方便很多: `int add(int a, int b) { return a + b;}` 不用处理这种类型判断
* 但仍有 deopt：
  * 虚方法内联
  * 类加载
  * 锁优化
* 回退更少、更稳定

👉 **Java JIT 也大量依赖 deopt**

---

## V8 为什么快（和 JIT 直接相关）

* 多层 JIT（Ignition + TurboFan）
* Hidden Class + Inline Cache
* 极端激进的投机优化
* 非常强的 deopt 系统

👉 **本质：把 JS 运行时“还原”为接近静态语言**
