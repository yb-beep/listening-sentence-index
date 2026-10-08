// 交付前自检：确认生成的单文件 HTML 没坏、能播放、按钮都在。
//   node check_page.js <单文件.html> [期望句数]
// jsdom 装了会做真实 DOM 行为测试；没装就退化为静态检查（仍然能抓出大部分问题）。

const fs = require('fs');
const path = require('path');

const FILE = process.argv[2];
const EXPECT = parseInt(process.argv[3] || '0', 10);
if (!FILE) { console.error('用法: node check_page.js <文件.html> [期望句数]'); process.exit(2); }

const html = fs.readFileSync(FILE, 'utf8');
let fail = 0;
const ok = (c, m) => { console.log((c ? '  PASS  ' : '  FAIL  ') + m); if (!c) fail++; };

console.log('静态检查：' + path.basename(FILE));
ok(!html.includes('__TITLE__'), '标题占位符已替换');
ok(!html.includes('__STORE_KEY__'), '存储键占位符已替换');
ok(!html.includes('__CLIPS__'), '音频数组已注入');

const m = html.match(/var CLIPS\s*=\s*(\[)/) || html.match(/CLIPS\s*=\s*(\[)/);
ok(!!m, '找到音频数组 CLIPS');
let nClips = 0;
if (m) {
  // 只数顶层元素个数，避免把整个 10MB 串读进来做 JSON.parse
  const start = html.indexOf(m[1], m.index);
  let depth = 0, inStr = false, esc = false, cnt = 0;
  for (let i = start; i < html.length; i++) {
    const c = html[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === '"') { inStr = false; cnt++; }
      continue;
    }
    if (c === '"') inStr = true;
    else if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) break; }
  }
  nClips = cnt;
  ok(nClips > 0, `音频片段数 = ${nClips}`);
  if (EXPECT) ok(nClips === EXPECT, `音频片段数与句子数一致（期望 ${EXPECT}）`);
}
const nRows = (html.match(/<tr class="row"/g) || []).length;   // 只数表格行，避开控制面板的 .row
ok(nRows === nClips, `表格行数(${nRows}) = 音频数(${nClips})`);

for (const [cls, label] of [['class="play"', '播放按钮'], ['class="veil"', '显示原文按钮'],
                            ['class="st"', '星标按钮'], ['class="pin"', '重新遮住按钮'],
                            ['class="secplay"', '板块连播按钮'], ['id="dictIn"', '听写输入框']]) {
  ok(html.includes(cls), `存在${label}`);
}

let jsdom = null;
try { jsdom = require('jsdom'); } catch (e) { /* 未安装则跳过 */ }
if (!jsdom) {
  console.log('\n（未安装 jsdom，跳过 DOM 行为测试。装法：npm i jsdom）');
  console.log(fail ? `\n✗ ${fail} 项未通过` : '\n✓ 静态检查全部通过');
  process.exit(fail ? 1 : 0);
}

const { JSDOM } = jsdom;
const POLY = `<script>
Object.defineProperty(window.HTMLMediaElement.prototype,'play',{value:function(){this.paused=false;window.__plays=(window.__plays||0)+1;return Promise.resolve();},writable:true,configurable:true});
Object.defineProperty(window.HTMLMediaElement.prototype,'pause',{value:function(){this.paused=true;},writable:true,configurable:true});
(function(){const A=window.Audio;window.Audio=function(){const a=new A();window.__aud=a;return a;};})();
window.scrollTo=function(){};window.alert=m=>{window.__alert=m;};window.confirm=()=>true;
window.__store={};
Object.defineProperty(window,'localStorage',{configurable:true,value:{
  getItem:k=>(k in window.__store?window.__store[k]:null),
  setItem:(k,v)=>{window.__store[k]=String(v);},
  removeItem:k=>{delete window.__store[k];}}});
URL.createObjectURL=()=> 'blob:test'; URL.revokeObjectURL=function(){};
HTMLAnchorElement.prototype.click=function(){};
</script>`;

const dom = new JSDOM(html.replace('<head>', '<head>' + POLY),
  { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, D = w.document;

setTimeout(() => {
  console.log('\nDOM 行为测试：');
  const rows = [...D.querySelectorAll('tr.row')];
  ok(rows.length === nClips, `渲染出 ${rows.length} 行`);

  rows[0].querySelector('.play').click();
  ok(w.__plays >= 1, '点击播放触发了一次播放');

  const veil = rows[0].querySelector('.veil');
  veil.click();
  const en = rows[0].querySelector('.en');
  ok(!!en && w.getComputedStyle(en).display !== 'none', '点「显示原文」后原文可见');

  const pin = rows[0].querySelector('.pin');
  pin.click();
  ok(w.getComputedStyle(en).display === 'none', '点「重新遮住」后原文重新隐藏');

  rows[1].querySelector('.st').click();
  ok(rows[1].className.includes('star') || rows[1].dataset.star === '1'
     || JSON.stringify(w.__store).includes('star'), '星标被记录');

  ok(Object.keys(w.__store).length > 0, 'localStorage 有写入（学习进度可保存）');

  const sel = D.querySelector('#from') || D.querySelector('input.inp');
  ok(!!sel, '存在区间/参数输入控件');

  console.log(fail ? `\n✗ ${fail} 项未通过` : '\n✓ 全部通过');
  process.exit(fail ? 1 : 0);
}, 400);
