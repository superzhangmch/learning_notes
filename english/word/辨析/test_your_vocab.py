import re
import json
import random
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional
from flask import Flask, render_template_string

app = Flask(__name__)

DATA_FILE = "形似.md"
BLANK = "_____"
FUZZY_THRESHOLD = 0.85

# ---------- 文本清洗与形变 ----------
def strip_zh_and_parens(s: str) -> str:
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'（[^）]*）', '', s)
    s = re.sub(r'[\u3000-\u303f\uff00-\uffef\u4e00-\u9fff]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s+([,.!?;:])', r'\1', s)
    return s

def ends_with_cvc(w: str) -> bool:
    vowels = "aeiou"
    if len(w) < 3: return False
    c1, v, c2 = w[-3], w[-2], w[-1]
    return (c1 not in vowels) and (v in vowels) and (c2 not in vowels) and c2 not in 'wy'

def gen_inflections(w: str):
    base = w.lower()
    forms = {base}
    if re.search(r'(s|x|z|ch|sh|o)$', base): forms.add(base + 'es')
    elif re.search(r'[^aeiou]y$', base): forms.add(base[:-1] + 'ies')
    else: forms.add(base + 's')
    if base.endswith('e'): forms.add(base + 'd')
    elif re.search(r'[^aeiou]y$', base): forms.add(base[:-1] + 'ied')
    elif ends_with_cvc(base): forms.update({base + base[-1] + 'ed', base + 'ed'})
    else: forms.add(base + 'ed')
    if base.endswith('ie'): forms.add(base[:-2] + 'ying')
    elif base.endswith('e') and not base.endswith(('ee','ye','oe')): forms.add(base[:-1] + 'ing')
    elif ends_with_cvc(base): forms.update({base + base[-1] + 'ing', base + 'ing'})
    else: forms.add(base + 'ing')
    return sorted(forms | {f.capitalize() for f in forms} | {f.upper() for f in forms})

def find_best_match(word, sentence):
    m = re.search(rf'\b{re.escape(word)}\b', sentence, flags=re.IGNORECASE)
    if m: return m.start(), m.end(), m.group(0)
    for f in gen_inflections(word):
        m = re.search(rf'\b{re.escape(f)}\b', sentence)
        if m: return m.start(), m.end(), m.group(0)
    tokens = [(m.group(0), m.span()) for m in re.finditer(r"[A-Za-z]+'?[A-Za-z]*", sentence)]
    best = (0.0, None)
    for tok, span in tokens:
        for f in [word] + gen_inflections(word):
            r = SequenceMatcher(a=tok.lower(), b=f.lower()).ratio()
            if r > best[0]:
                best = (r, (span[0], span[1], tok))
    if best[0] >= FUZZY_THRESHOLD and best[1]:
        return best[1]
    return None

# ---------- 解析含释义 ----------
def parse_text_grouped(text: str):
    groups = []
    cur_group = None
    cur_word = None
    for raw in text.splitlines():
        m_h = re.match(r'^###\s*(.+?)\s*$', raw)
        if m_h:
            cur_group = {'title': m_h.group(1), 'options': [], 'examples': {}}
            groups.append(cur_group)
            cur_word = None
            continue
        if cur_group is None: continue

        m_opt = re.match(r'^- ([A-Za-z]+)\s*(.*)', raw)
        if m_opt:
            word = m_opt.group(1)
            meaning = m_opt.group(2).strip()
            cur_word = word
            cur_group['options'].append({'word': word, 'meaning': meaning})
            cur_group['examples'].setdefault(word, [])
            continue

        if cur_word and re.match(r'^ {2}- ', raw):
            content = raw[3:].lstrip()
            if not content.startswith('#'):
                cur_group['examples'][cur_word].append(content)
            continue
    return groups

def build_mcqs_grouped(text: str):
    groups = parse_text_grouped(text)
    questions = []
    for g in groups:
        opts = g['options']
        for opt in opts:
            word = opt['word']
            for ex in g['examples'].get(word, []):
                sent = strip_zh_and_parens(ex)
                if not sent:
                    continue
                m = find_best_match(word, sent)
                if not m:
                    continue
                s, e, _ = m
                q_text = sent[:s] + BLANK + sent[e:]
                questions.append({'options': opts, 'answer': word, 'question': q_text})
    return questions

# ---------- Web ----------
try:
    with open(DATA_FILE, encoding="utf-8") as f:
        ALL_QUESTIONS = build_mcqs_grouped(f.read())
except Exception as e:
    ALL_QUESTIONS = []
    print("[ERROR]", e)

@app.route("/")
def index():
    return '<h3>访问 <a href="/quiz">/quiz</a> 开始测验</h3>'

@app.route("/quiz")
def quiz():
    if not ALL_QUESTIONS:
        return "<p>题库为空，请检查 形似.md 是否存在且格式正确。</p>"
    sample = random.sample(ALL_QUESTIONS, min(10, len(ALL_QUESTIONS)))
    data_json = json.dumps(sample, ensure_ascii=False)
    html = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>形似测验</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial;
max-width:900px;margin:40px auto;background:#fafafa;line-height:1.6;color:#222;}}
.card{{background:#fff;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 4px 15px rgba(0,0,0,.06);}}
.question{{margin-bottom:15px;}}
.options{{display:flex;flex-wrap:wrap;gap:10px 18px;margin-top:8px;}}
.opt{{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;background:#f6f8fb;}}
.opt input{{margin:0;}}
.opt .lbl{{font-weight:600;color:#2b5faa;}}
.btn{{background:#2b6cb0;color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:600;}}
.btn:disabled{{opacity:.6;cursor:not-allowed;}}
.correct{{color:#0a7f2e;font-weight:600;}}
.wrong{{color:#c62828;font-weight:600;}}
.answer-reveal{{margin-top:6px;}}
.meanings{{margin-top:8px;padding-left:10px;border-left:3px solid #e0e0e0;font-size:15px;color:#333;}}
.meanings li{{margin-bottom:4px;}}
.score{{font-size:18px;font-weight:700;margin-top:10px;}}
</style>
</head>
<body>
<h2>形似单词测验（随机10题）</h2>
<div id="quiz"></div>
<div>
  <button class="btn" id="submitBtn" onclick="submitQuiz()">提交</button>
  <button class="btn" onclick="location.reload()">再来一组</button>
  <span id="score" class="score"></span>
</div>

<script>
const data = {data_json};
function shuffle(a){{for(let i=a.length-1;i>0;i--){{const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}}return a;}}

function buildQuiz(){{
  const root=document.getElementById('quiz');
  data.forEach((q,i)=>{{
    const opts=shuffle([...q.options]);
    const letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    const htmlOpts=opts.map((opt,idx)=>`
      <label class="opt">
        <span class="lbl">${{letters[idx]}}.</span>
        <input type="radio" name="q${{i}}" value="${{opt.word}}">
        <span>${{opt.word}}</span>
      </label>`).join('');
    root.innerHTML+=`
      <div class="card question">
        <div><b>Q${{i+1}}.</b> ${{q.question}}</div>
        <div class="options">${{htmlOpts}}</div>
        <div class="answer-reveal" id="rev-${{i}}"></div>
      </div>`;
  }});
}}

function submitQuiz(){{
  let correct=0;
  data.forEach((q,i)=>{{
    const chosen=(document.querySelector(`input[name='q${{i}}']:checked`)||{{}}).value||null;
    const rev=document.getElementById(`rev-${{i}}`);
    if(chosen===q.answer){{correct++;rev.innerHTML=`<span class='correct'>✔ 正确：${{q.answer}}</span>`;}}
    else{{const pick=chosen?`（你选：${{chosen}}）`:'（未作答）';rev.innerHTML=`<span class='wrong'>✘ 正确：${{q.answer}}</span> <span class='sub'>${{pick}}</span>`;}}

    // 添加词义复盘
    const meanings=q.options.map(o=>`<li><b>${{o.word}}</b> — ${{o.meaning}}</li>`).join('');
    rev.innerHTML += `<ul class='meanings'>${{meanings}}</ul>`;
  }});
  document.getElementById('score').textContent=`得分：${{correct}} / ${{data.length}}`;
  document.getElementById('submitBtn').disabled=true;
}}

buildQuiz();
</script>
</body>
</html>
"""
    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True)

