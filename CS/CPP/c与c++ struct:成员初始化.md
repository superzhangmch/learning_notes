# c 与 c++ struct:成员初始化

浏览linux 代码时发现了这样的东西：

```
     67 static struct linux_binfmt elf_format = {
     68               .module        = THIS_MODULE,
     69               .load_binary   = load_elf_binary,
     70               .load_shlib     = load_elf_library,
     71               .core_dump     = elf_core_dump,
     72               .min_coredump   = ELF_EXEC_PAGESIZE,
     73               .hasvdso       = 1
     74 };
```

不明白什么意思，后来才恍然大悟，这不就是给 linux_binfmt 这个struct的各个字段初始化嘛。

试验发现，确实是这么回事，实际上linux_binfmt 都有定义：

```
     78 struct linux_binfmt {
     79        struct list_head lh;
     80        struct module *module;
     81        int (*load_binary)(struct linux_binprm *, struct  pt_regs * regs);
     82        int (*load_shlib)(struct file *);
     83        int (*core_dump)(long signr, struct pt_regs *regs, struct file *file, unsigned long limit);
     84        unsigned long min_coredump;   
     85        int hasvdso;
     86 };
```

但是试验的时候发现， 只有c才可以这样用，c++是不可以这样用的。

先记载这些，详情再补。

