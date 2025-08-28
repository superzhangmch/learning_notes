<img width="478" height="870" alt="image" src="https://github.com/user-attachments/assets/c234b51e-0f8b-4ca6-b115-74296782d1f6" />

### CUDA 是 NVIDIA 自家的 编程平台 + 驱动 API，它才是真正能直接调度 GPU 硬件的接口。

内存分配（cudaMalloc）、数据拷贝（cudaMemcpy）、kernel 启动（<<<>>>）、流与事件等，都直接通过 CUDA runtime/driver 实现。

个人写的 CUDA C/C++ kernel 会被编译成 PTX → SASS 指令，最终在 GPU SM 上执行。

所以可以说：只有 CUDA 直接操作 GPU 硬件。

- cuBLAS：只是把矩阵乘等操作实现好了，内部还是调用 CUDA kernel。
- cuDNN：深度学习常用算子库（卷积、池化等），内部也调用 CUDA kernel，有时还会调 cuBLAS。
- Transformer Engine (TE)：高层封装，帮你管理 FP8 精度和缩放，内部依赖 cuBLASLt/cuDNN → CUDA。
