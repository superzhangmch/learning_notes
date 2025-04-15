![image](https://github.com/user-attachments/assets/51282531-5e7b-45e4-9dc7-6be61cbbbb3c)

单条数据的 G 个不同采样，决定出一个平均 reward。然后可以用它来得到G个采样各自的 advantage。


![image](https://github.com/user-attachments/assets/919ffe18-2d26-4242-9a4e-081c1860891f)

GRPO 中把 KL 项独立了出来，就不能通过蒙特卡洛采样来算了（否则只用 log(../..) 一项就行了）。但是有它的 unbiased estimator 估计，拿它来算即可。


![image](https://github.com/user-attachments/assets/5dfd14e7-faae-438c-99b4-ad97b3122cd7)
