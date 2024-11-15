# HTML table的田形与井形单线CSS格式化

HTML简单展示复杂结构化数据，用TABLE是一种很好的方式：可以table嵌table。对于外层table，需要所有线条都显示，内部table，井字形状显示。
假设表格只由TD组成，则可用以下实现：
```
table th,td {border-collapse:collapse; border:1px solid green; padding-left:5px;padding-right:5px; font-size:12px;}
     
table.sharp { border-collapse: collapse; border: 0;  padding:0px;margin:0px;}
table.sharp td { border: 1px solid green; padding: 5px;
        border-bottom: none;
        border-right: none;
    }
table.sharp tr:first-child td { border-top: none; }    
table.sharp tr td:first-child { border-left: none; }
```
