参：https://arxiv.org/pdf/2408.13006v1 《Systematic Evaluation of LLM-as-a-Judge in LLM Alignment Tasks: Explainable Metrics and Diverse Prompt Templates》

如果用  LLM 作为 judge，一般需要 temperature取得较小，openCompass 中用了 0. 该文章中说应该尽量小，所以它用了0.1
以下来自AI总结：

### **Summary of Temperature Settings and Findings in the Paper**

#### **Temperature Settings**
1. The paper evaluates the impact of the **temperature parameter** on **self-consistency** and **accuracy** when using LLMs as judges.
2. Five different temperatures were tested: **0.0, 0.1, 0.3, 0.5, and 0.7**.
3. Experiments involved:
   - Running LLM judges on 1000 samples across five data splits.
   - Asking LLM judges to choose the better response **five times per sample**.
   - Measuring **self-consistency rate (SCR)** and **accuracy (Accboth)** for each temperature setting.

#### **Findings on Temperature Impact**
1. **Higher temperatures reduce self-consistency**:  
   - As temperature increases, the likelihood of the LLM judge making **inconsistent** decisions rises.
   - Even at **temperature = 0.0**, complete self-consistency (**SCR = 1.0**) was **not** achieved.

2. **Accuracy is not significantly affected by temperature**:  
   - Accuracy fluctuates only slightly across different temperature values.
   - The performance difference in accuracy between **0.0 and 0.7** is minimal.

3. **Temperature = 0.1 was chosen as the optimal setting**:  
   - It provides **the highest level of self-consistency** while avoiding full determinism (0.0).
   - This value is not a special case (e.g., 0.0) and allows for **some variability**.

#### **Key Conclusion**
- **Temperature 0.1** was selected for all experiments as it **balances consistency and variability**.
- **Lower temperatures** ensure more **consistent judgments**, but **do not eliminate inconsistencies** completely.
- The study confirms that **higher temperatures lead to more randomization, reducing self-consistency** but **not significantly affecting accuracy**.
