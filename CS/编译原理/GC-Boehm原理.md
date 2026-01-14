by claude

Boehm GC 用的是保守式 GC（Conservative GC），它的工作原理很巧妙但有局限性。

### 🔍 Boehm GC 如何找到"不再使用"的对象

  核心原理：保守式扫描

  Boehm GC 不依赖类型信息，而是把内存中所有"看起来像指针"的值都当作指针来处理。

  📋 工作流程

  1️⃣ 找到所有"根"（Roots）
```
  // GC 触发时，扫描这些区域：

  ┌─────────────────┐
  │  CPU 寄存器      │ ← 扫描所有寄存器的值
  ├─────────────────┤
  │  栈空间          │ ← 扫描从栈底到栈顶的所有值
  ├─────────────────┤
  │  全局变量        │ ← 扫描 .data 和 .bss 段
  ├─────────────────┤
  │  静态变量        │ ← 扫描静态数据区
  └─────────────────┘
```

  示例：
  ```
  void foo() {
      char *str = GC_malloc(100);  // 分配对象A
      int x = 12345;                // 普通整数
      char *arr = GC_malloc(50);   // 分配对象B

      // GC 触发时，扫描栈：
      // 栈上有：str指针、12345、arr指针
  }

  // GC 会检查栈上的每个字（word），看它是否指向堆中的对象
  ```
  2️⃣ 保守式指针识别
```
  // 对栈上的每个值，GC 会问：
  bool is_pointer(void *value) {
      // 1. 值是否在堆地址范围内？
      if (value < heap_start || value >= heap_end)
          return false;  // 不在堆内，肯定不是指针

      // 2. 值是否指向某个已分配对象的起始位置或内部？
      GCObject *obj = find_object_containing(value);
      if (obj != NULL)
          return true;  // 可能是指针！

      return false;
  }
```
  关键点：Boehm GC 不知道这个值真的是指针还是碰巧像指针的整数。

  3️⃣ 递归标记
```
  void mark_phase() {
      // 1. 扫描所有根区域
      scan_registers();
      scan_stack();
      scan_globals();

      // 2. 对每个"可能的指针"
      for (each possible_pointer in roots) {
          GCObject *obj = find_object(possible_pointer);
          if (obj && !obj->marked) {
              obj->marked = true;

              // 3. 递归扫描这个对象内部
              scan_object_interior(obj);  // 找对象内部的指针
          }
      }
  }
```
  4️⃣ 清除未标记的对象
```
  void sweep_phase() {
      for (each object in heap) {
          if (!object->marked) {
              // 这个对象从任何根都访问不到
              free(object);  // 回收它
          } else {
              object->marked = false;  // 清除标记，准备下次GC
          }
      }
  }
```
  🎯 具体例子
```
  #include <gc.h>

  int main() {
      // 场景1：对象仍在使用
      char *str1 = GC_malloc(100);  // 对象A
      strcpy(str1, "hello");

      // GC 触发
      GC_gcollect();
      // 结果：str1 在栈上 → 对象A被标记 → 对象A存活

      printf("%s\n", str1);  // ✅ 正常工作


      // 场景2：对象不再使用
      char *str2 = GC_malloc(100);  // 对象B
      strcpy(str2, "world");
      str2 = NULL;  // 放弃引用

      // GC 触发
      GC_gcollect();
      // 结果：栈上没有指向对象B的指针 → 对象B未被标记 → 对象B被回收


      // 场景3：间接引用
      typedef struct {
          char *name;
          int age;
      } Person;

      Person *p = GC_malloc(sizeof(Person));
      p->name = GC_malloc(50);  // 对象C
      strcpy(p->name, "Alice");

      // GC 触发
      GC_gcollect();
      // 结果：
      // 1. p 在栈上 → Person对象被标记
      // 2. 扫描 Person 内部 → 发现 p->name → 对象C被标记
      // 3. 两个对象都存活
  }
```
  ⚠️ 保守式 GC 的问题

  问题1：假阳性（False Positive）
```
  int main() {
      char *ptr = GC_malloc(1000);  // 分配对象，地址假设是 0x12345000
      ptr = NULL;  // 不再使用

      int random = 0x12345000;  // 碰巧这个整数值等于刚才的地址！

      // GC 触发
      GC_gcollect();
      // 问题：GC 扫描栈时，看到 0x12345000
      //      它认为这是指向对象的指针！
      //      对象无法被回收 → 内存泄漏
  }
```
  后果：某些对象可能永远无法回收（但很少见）

  问题2：无法移动对象
```
  // 精确式 GC（如 Java）可以：
  void* ptr = gc_alloc(100);
  // GC 时可以移动对象到新位置，压缩堆
  ptr = new_address;  // 更新指针

  // Boehm GC 不行：
  void* ptr = GC_malloc(100);
  int x = (int)ptr;  // 如果整数保存了地址
  // GC 不知道 x 是指针，无法移动对象
```
  后果：堆碎片化

  问题3：多线程寄存器扫描
```
  // 如果某个线程的寄存器保存了指针
  // GC 需要停止所有线程，扫描它们的寄存器
  // 复杂度高
```
  📊 Boehm GC vs 精确式 GC
```
  ┌──────────┬─────────────────┬──────────────────────────┐
  │   特性   │ Boehm GC (保守)  │ 精确式 GC (如你自己实现)    │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 类型信息  │ ❌ 不需要         │ ✅ 需要                  │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 指针识别  │ 猜测（保守）       │ 精确知道                  │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 假阳性    │ 可能有           │ ❌ 无                    │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 内存回收  │ 可能漏回收        │ ✅ 完全回收                │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 对象移动  │ ❌ 不能          │ ✅ 可以                   │
  ├──────────┼─────────────────┼──────────────────────────┤
  │ 集成难度  │ ⭐ 简单          │ ⭐⭐⭐ 复杂                │
  └──────────┴─────────────────┴──────────────────────────┘
```
  🔬 Boehm GC 扫描示例

```
  #include <gc.h>
  #include <stdio.h>

  void demo() {
      // 栈布局（假设）
      // +----------------+  高地址
      // | 返回地址       |
      // | 保存的 ebp     |
      // | ptr1           |  ← 0xAAAA1000 (真指针)
      // | random_int     |  ← 0xAAAA2000 (碰巧像地址)
      // | ptr2           |  ← 0xAAAA3000 (真指针)
      // | local_var      |  ← 42 (整数)
      // +----------------+  低地址 (栈顶)

      char *ptr1 = GC_malloc(100);   // 0xAAAA1000
      int random_int = 0xAAAA2000;   // 恰好在堆范围内
      char *ptr2 = GC_malloc(100);   // 0xAAAA3000
      int local_var = 42;

      GC_gcollect();

      // GC 扫描过程：
      // 1. 扫描栈：0xAAAA1000 → 可能是指针 → 找到对象 → 标记
      // 2. 扫描栈：0xAAAA2000 → 可能是指针 → 找到对象 → 标记（误判！）
      // 3. 扫描栈：0xAAAA3000 → 可能是指针 → 找到对象 → 标记
      // 4. 扫描栈：42         → 不在堆范围  → 跳过
  }
```
