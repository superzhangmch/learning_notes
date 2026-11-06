一种特殊的 OPT 是, student 与 teacher 都是同一个 model, 这时候可以自我蒸馏.

这类方法的思路是: model 采样生成了结果: [req, response], 中间插入一些指导性的语句, 构成: [req, 指导text, response], 然后用 model 对 [req, 指导text, response] 过一遍forward, 从而得到了 response 的新的 logits: 他们可以当作是 teacher 的 logits, 用来做 OPT 蒸馏 [req, response].

这个“指导text”, 可能是一些example, 也可能是一些通过某些手段获得的 req->response 的反馈信息(比如, 不应该如何如何), 这样 model 看到了 “[req, 指导]” 之后, 就可以对 response 打出更客观的 logits. 于是该方法才有效. 

该方法, 可叫之 privileged information distillation. 
