# 关于 AVX 指令能加速多少倍

AVX指令可以一次处理8个浮点数，按理说比原生会提速8倍，但经测试只有不到4倍提速。

经研究发现，问题在于 _mm256_load_ps /_mm256_store_ps 其实很费时间的。另外，是否32字节对齐与否，对性能影响不大。远不如 load、store的影响。当去掉store, load 后，单纯看AVX的提速，基本上是符合8倍提速的。因此用avx指令的时候，需要在一次load、store 中间尽量多插入一些别的操作，而不仅仅是一次简单的加减乘除。

另外注意AVX指令只支持基本浮点运算，要计算sin/cos/exp/log等，需用avx指令组合得出，一个实现是 http://software-lisc.fbk.eu/avx_mathfun/ 。至于tanh、sogmoid等，又需要进一步用exp等来实现了。

参考：
- avx指令集 http://blog.csdn.net/fengbingchun/article/details/23598709
- https://stackoverflow.com/questions/29089302/performance-avx-sse-assembly-vs-intrinsics


测试代码（来自网上，改了改）,暂存，免得哪天又要测试：
```
#include <stdio.h>
#include <sys/time.h>
#include <time.h>
#include <x86intrin.h>

int main() {
   const int col = 128, row = 1024*32, num_trails = 1;
   struct timeval tpstart, tpend;

   int align_size = 32;
   float * w1 = new float[row * col + align_size];
   float * x1 = new float[col + align_size];
   float * y1 = new float[row + align_size];

    // 字节对齐。这里128字节，看看按cpu cacheline对齐有没有好处。没发现。按32字节对齐也没发现提升
    // make all aligned. here align_size bytes 
   float (*w)[col] = (float(*)[col])((((unsigned long)w1) + 127) / align_size * align_size);
   float * x = (float*)((((unsigned long)x1) + 127) / align_size * align_size);
   float * y = (float*)((((unsigned long)y1) + 127) / align_size * align_size);
   for (int i=0; i<row; i++) {
       for (int j=0; j<col; j++) {
          w[i][j]=(float)(rand()00)/800.0f;
       }  
   }
   for (int j=0; j<col; j++) {
      x[j]=(float)(rand()00)/800.0f;
   }

    // The original matrix multiplication version
   gettimeofday(&tpstart,NULL);
   for (int r = 0; r < num_trails; r++)
       for(int j = 0; j < row; j++)
       {  
          float sum = 0;
          float *wj = w[j];

          for(int i = 0; i < col; i++)
              sum += wj[i] * x[i];

          y[j] = sum;
       }  
   gettimeofday(&tpend,NULL); int us_used=((tpend.tv_sec-tpstart.tv_sec)*1000000+(tpend.tv_usec-tpstart.tv_usec)); printf("tm used %d\n", us_used);

   for (int i=0; i<10; i++) {
       printf("%.4f, ", y[i]);
   }
   printf("\n");
    // The avx matrix multiplication version.
   gettimeofday(&tpstart,NULL);


    // 如果不 load，则效果发现确实能差不多8倍的样子；否则4倍的样子 
    #define DO_ACTION(vec1, j, vec2) do { \
       mb0 = _mm256_load_ps(vec1 + j); \
       mc0 = _mm256_mul_ps(vec2, mb0); \
       ms0 = _mm256_add_ps(ms0, mc0);\
    } while(0);

   __m256 ma0 = _mm256_load_ps(x); 
   __m256 ms0 = _mm256_setzero_ps();
   __m256 mb0 = _mm256_setzero_ps();
   __m256 mc0 = _mm256_setzero_ps();
   for (int i=0; i<row; i++) {
       for (int j = 0; j < col; j += 8*8) {
          //  循环展开，没发现效果
          DO_ACTION(w[i], j+0, ma0);
          DO_ACTION(w[i], j+1, ma0);
          DO_ACTION(w[i], j+2, ma0);
          DO_ACTION(w[i], j+3, ma0);
          DO_ACTION(w[i], j+4, ma0);
          DO_ACTION(w[i], j+5, ma0);
          DO_ACTION(w[i], j+6, ma0);
          DO_ACTION(w[i], j+7, ma0);
          //DO_ACTION(w[i], j+8, ma0);
          //DO_ACTION(w[i], j+9, ma0);
          //DO_ACTION(w[i], j+10, ma0);
          //DO_ACTION(w[i], j+11, ma0);
          //DO_ACTION(w[i], j+12, ma0);
          //DO_ACTION(w[i], j+13, ma0);
          //DO_ACTION(w[i], j+14, ma0);
          //DO_ACTION(w[i], j+15, ma0);
       }
   }
gettimeofday(&tpend,NULL); us_used=((tpend.tv_sec-tpstart.tv_sec)*1000000+(tpend.tv_usec-tpstart.tv_usec)); printf("tm used %d\n", us_used);
printf("<%f>\n", ms0[0]);
}
```
