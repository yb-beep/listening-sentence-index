# -*- coding: utf-8 -*-
"""单文件精听页的 HTML / CSS / JS 模板（由 make_single.py 装配）"""

HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f5f6f8;color:#1c2024;
font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:18px 16px 140px}
h1{font-size:20px;margin:0 0 4px}
.sub2{color:#6b7280;font-size:12.5px;margin-bottom:12px}
.panel{background:#fff;border:1px solid #e2e6ea;border-radius:12px;padding:12px 14px;
box-shadow:0 1px 3px rgba(16,24,40,.05)}
.sticky{position:sticky;top:0;z-index:20;margin-bottom:12px}
.panel.folded .row:not(:first-child){display:none}
.grow{flex:1;min-width:8px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.row+.row{margin-top:9px;padding-top:9px;border-top:1px dashed #e6e9ed}
.lab{font-size:12.5px;color:#6b7280;margin-right:2px}
.seg{display:inline-flex;border:1px solid #d8dee6;border-radius:8px;overflow:hidden}
.seg button{background:#fff;border:0;border-right:1px solid #e6e9ed;padding:6px 12px;
font-size:13px;color:#475569;cursor:pointer;font-family:inherit}
.seg button:last-child{border-right:0}
.seg button.on{background:#2563eb;color:#fff}
button.b{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:7px 13px;
font-size:13.5px;cursor:pointer;font-family:inherit}
button.b:hover{background:#1d4ed8}
button.b.gh{background:#fff;color:#334155;border:1px solid #d5dae1}
button.b.gh:hover{background:#f1f5f9}
button.b:active{transform:translateY(1px)}
button.b.grn,button.b.ok{background:#0e9f6e;color:#fff;border-color:#0e9f6e}
button.b.grn:hover,button.b.ok:hover{background:#0b8259}
button.b.red{background:#fff;color:#b91c1c;border:1px solid #e6c9c9}
button.b.red:hover{background:#fdf2f2}
select{font-family:inherit;font-size:13px;padding:5px 7px;
border:1px solid #d5dae1;border-radius:7px;background:#fff;color:#1c2024}
.inp{width:60px;padding:4px 6px;border:1px solid #d5dae1;border-radius:7px;
font-family:inherit;font-size:13.5px;text-align:center;color:#1c2024;background:#fff}
.inp::-webkit-outer-spin-button,.inp::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
.inp:focus{outline:none;border-color:#93b8f7;box-shadow:0 0 0 3px #e8f0fe}
.prog{font-size:12.5px;color:#6b7280;font-variant-numeric:tabular-nums}
.prog b{color:#2563eb;font-weight:500}
kbd{background:#f1f3f6;border:1px solid #dde1e6;border-bottom-width:2px;border-radius:4px;
padding:0 4px;font-size:11.5px;font-family:ui-monospace,Menlo,monospace;color:#475569}
.tip{font-size:12px;color:#98a1ab}
.nav{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 14px}
.nav a{background:#fff;border:1px solid #e2e6ea;color:#475569;border-radius:999px;
padding:4px 11px;font-size:12.5px;text-decoration:none}
.nav a:hover{background:#eef4ff;border-color:#c7d7fb;color:#1d4ed8}
.grp{background:#fff;border:1px solid #e2e6ea;border-radius:12px;margin-bottom:12px;overflow:hidden}
.grp h2{font-size:14.5px;margin:0;padding:10px 15px;background:#f3f5f8;border-bottom:1px solid #e8ebef;
display:flex;justify-content:space-between;align-items:center}
.grp h2 .n{color:#9aa3ad;font-weight:400;font-size:12px}
.grp h2 .secplay{background:#eef4ff;border:1px solid #cfdffb;color:#2563eb;border-radius:6px;
padding:3px 11px;font-size:12.5px;font-family:inherit;cursor:pointer;margin-right:10px}
.grp h2 .secplay:hover{background:#dbe7ff}
.grp h2 .lft{display:flex;align-items:center}
.secnav{padding:8px 15px;background:#fafbfc;border-top:1px solid #eef1f4;text-align:right}
.secplay2{background:#fff;border:1px solid #d5dae1;color:#334155;border-radius:7px;
padding:5px 12px;font-size:12.5px;font-family:inherit;cursor:pointer}
.secplay2:hover{background:#eef4ff;border-color:#cfdffb;color:#1d4ed8}
table{width:100%;border-collapse:collapse}
td{padding:8px 10px;border-bottom:1px solid #f2f4f6;vertical-align:top}
tr:last-child td{border-bottom:0}
tr.row:hover{background:#fafbfc}
tr.on{background:#e9f1ff}
tr.row.inrange{background:#f4f9ff}
tr.row.inrange td.idx{color:#1d4ed8;font-weight:600}
tr.heard td.idx{color:#2563eb}
tr.row.hide{display:none}
tr.row.star td.idx::after{content:"\\2605";color:#f59e0b;font-size:11px;margin-left:1px}
td.idx{color:#9aa3ad;width:44px;text-align:right;font-variant-numeric:tabular-nums;font-size:13px}
td.tm{width:96px;white-space:nowrap;color:#6b7280;font-size:12.5px}
.play{background:#eef4ff;border:1px solid #cfdffb;color:#2563eb;border-radius:6px;
width:30px;height:25px;cursor:pointer;font-size:11px;line-height:1;margin-right:6px;font-family:inherit}
.play:hover{background:#dbe7ff}
td.spk{width:48px}
.bd{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:5px;background:#eef2f7;color:#5b6570}
.bd.m{background:#e3f0ff;color:#1d4ed8}
.bd.w{background:#fdeaf3;color:#b4327c}
.bd.q{background:#fff3d6;color:#8a5a00}
.bd.x{background:#eef2f7;color:#8a929c}
td.tx{position:relative;padding-right:64px}
.en{font-size:14.8px;color:#111827}
.cn{font-size:13.2px;color:#6b7280;margin-top:2px}
.veil{display:none;width:100%;background:repeating-linear-gradient(45deg,#f1f3f6,#f1f3f6 8px,#e9edf1 8px,#e9edf1 16px);
border:1px dashed #cbd3dd;border-radius:7px;padding:6px 10px;color:#7b8590;font-size:12.5px;
cursor:pointer;text-align:left;font-family:inherit}
.veil:hover{background:#eaf1fb;border-color:#a9c6f5;color:#1d4ed8}
.pin,.st{position:absolute;background:#fff;border:0;cursor:pointer;
font-size:13px;opacity:.3;padding:2px 4px;border-radius:5px;font-family:inherit;line-height:1}
.pin{right:8px;top:8px}
.st{right:32px;top:8px}
.pin:hover,.st:hover{opacity:1;background:#eef2f7}
tr.row.star .st{opacity:1;color:#f59e0b}
.warn{display:none;background:#fff5f5;border:1px solid #f3c9c9;color:#8a2b2b;
border-radius:10px;padding:10px 14px;font-size:13px;margin-bottom:12px}
body.m-none tr.row td.tx .en,body.m-none tr.row td.tx .cn{display:none}
body.m-none tr.row td.tx .veil{display:block}
body.m-none tr.row.rev td.tx .en,body.m-none tr.row.rev td.tx .cn{display:block}
body.m-none tr.row.rev td.tx .veil{display:none}
body.m-cn tr.row td.tx .en{display:none}
body.m-cn tr.row td.tx .veil{display:none}
body.m-all tr.row td.tx .veil{display:none}
body.pm-stage tr.row.rev td.tx .cn{display:none}
body.pm-stage tr.row.rev.cn-on td.tx .cn{display:block}
.dwrap{position:sticky;bottom:0;margin-top:14px;background:#fff;border:1px solid #d5dae1;
border-radius:12px;padding:12px 14px;box-shadow:0 -2px 10px rgba(16,24,40,.06);display:none}
.dwrap.on{display:block}
.dwrap .dh{font-size:12.5px;color:#6b7280;margin-bottom:7px}
.dwrap textarea{width:100%;min-height:56px;font:inherit;font-size:14px;padding:8px 10px;
border:1px solid #d5dae1;border-radius:8px;resize:vertical}
.dwrap textarea:focus{outline:none;border-color:#93b8f7;box-shadow:0 0 0 3px #e8f0fe}
.dres{margin-top:8px;font-size:14px;line-height:1.9}
.dres .ok{color:#166534}
.dres .bad{color:#b91c1c;text-decoration:line-through}
.dres .fix{color:#166534;font-weight:500}
.dres .miss{color:#b45309;border-bottom:1px dashed #d9a441}
.foot{margin-top:16px;color:#9aa3ad;font-size:12px;text-align:center}
</style></head><body class="m-none"><div class="wrap">
<h1>__TITLE__</h1>
<div class="sub2" id="meta"></div>
<div class="warn" id="warn"></div>
<div class="panel sticky">
  <div class="row">
    <span class="lab">原文显示</span>
    <div class="seg" id="modes">
      <button data-m="none" class="on">全部隐藏</button>
      <button data-m="cn">仅中文</button>
      <button data-m="all">中英全显</button>
    </div>
    <button class="b gh" id="showHere">显示本句</button>
    <button class="b gh" id="resetVeil">全部重新遮住</button>
    <span class="prog" id="prog"></span>
    <span class="grow"></span>
    <button class="b gh" id="fold">收起面板 &#9650;</button>
  </div>
  <div class="row">
    <button class="b" id="playBtn">播放 / 暂停</button>
    <button class="b gh" id="prevBtn">上一句</button>
    <button class="b gh" id="nextBtn">下一句</button>
    <button class="b gh" id="stopBtn">停止</button>
    <span class="lab">每句</span>
    <select id="repeat">
      <option value="1" selected>播 1 遍</option><option value="2">播 2 遍</option>
      <option value="3">播 3 遍</option><option value="-1">循环本句</option>
    </select>
    <span class="lab">句间</span>
    <select id="gap">
      <option value="0" selected>0 秒</option><option value="1000">1 秒</option>
      <option value="2000">2 秒</option><option value="3000">3 秒</option>
    </select>
    <span class="lab">速度</span>
    <select id="rate">
      <option value="0.6">0.6x</option><option value="0.75">0.75x</option>
      <option value="0.9">0.9x</option><option value="1" selected>1.0x</option>
      <option value="1.2">1.2x</option>
    </select>
    <input type="checkbox" id="autoRev"> <span class="lab">播完自动显示原文</span>
  </div>
  <div class="row">
    <span class="lab">连播范围</span>
    <select id="scope">
      <option value="range" selected>自定义区间</option>
      <option value="all">全篇 1 → 末句</option>
    </select>
    第 <input type="number" class="inp" id="fromN" min="1" value="1">
    — 第 <input type="number" class="inp" id="toN" min="1" value="5"> 句
    <button class="b" id="playRange">▶ 连播</button>
    <button class="b gh" id="loopRange">↻ 循环区间</button>
    <button class="b gh" id="setFrom">当前句作起点</button>
    <button class="b gh" id="setTo">当前句作终点</button>
    <button class="b gh" id="clearRange">清空</button>
    <span class="lab">每组</span>
    <select id="grpSize">
      <option value="1" selected>逐句</option><option value="2">2 句</option>
      <option value="3">3 句</option><option value="5">5 句</option>
    </select>
    <select id="grpRep">
      <option value="1" selected>啃 1 遍</option><option value="2">啃 2 遍</option>
      <option value="3">啃 3 遍</option>
    </select>
    <span class="tip">Shift + 点某行 = 依次指定起点 / 终点</span>
  </div>
  <div class="row">
    <span class="lab">练习流程</span>
    <select id="practice">
      <option value="manual" selected>手动：我自己控制</option>
      <option value="stage">三阶段：盲听 → 看英文 → 看中文</option>
      <option value="dict">听写：打字后自动校对</option>
    </select>
    <span class="lab">筛选</span>
    <select id="filter">
      <option value="all" selected>全部句子</option>
      <option value="star">只看星标 ☆</option>
      <option value="todo">只看没听过的</option>
      <option value="done">只看听过的</option>
    </select>
    <span class="prog" id="finfo"></span>
    <button class="b gh" id="starAll">星标当前区间</button>
    <button class="b red" id="wipe">清空学习记录</button>
  </div>
  <div class="row">
    <span class="lab">导出</span>
    <button class="b gh" id="dlRange">⬇ 区间合并音频</button>
    <button class="b gh" id="dlZip">⬇ 全部音频 + Anki 导入包 (zip)</button>
    <button class="b gh" id="dlTxt">⬇ 中英对照文本</button>
    <span class="tip" id="exTip"></span>
  </div>
  <div class="row" style="color:#6b7280;font-size:12.5px">
    点 ▶ 播放单句，点灰色斜纹条看原文，点整行也能播，☆ 标难句。
    快捷键 <kbd>&darr;</kbd><kbd>&uarr;</kbd> 切句 · <kbd>空格</kbd> 播放/重播 ·
    <kbd>H</kbd> 切换显隐 · <kbd>S</kbd> 显示本句 · <kbd>F</kbd> 星标 ·
    <kbd>R</kbd> 连播当前范围 · <kbd>Esc</kbd> 停止
  </div>
</div>
<div class="nav" id="nav"></div>
"""

DICT_BAR = """
<div class="dwrap" id="dictBar">
  <div class="dh" id="dictHead">听写第 ? 句</div>
  <textarea id="dictIn" placeholder="把你听到的英文打在这里，回车提交"></textarea>
  <div class="row" style="margin-top:8px">
    <button class="b" id="dictOk">提交校对</button>
    <button class="b gh" id="dictSkip">跳过看下句</button>
    <button class="b gh" id="dictTip">提示一个词</button>
    <span class="tip" id="dictHint">回车提交；校对后再按回车进入下一句</span>
  </div>
  <div class="dres" id="dictRes"></div>
</div>
"""

TAIL = """
<div class="foot">音频已全部内嵌在本文件中 · 可单独拷到任何地方打开 · 无需联网</div>
</div>
<script>
const CLIPS = __CLIPS__;
const ROWS = Array.from(document.querySelectorAll('tr.row'));
const NROW = ROWS.length;
const KEY = '__STORE_KEY__';
const aud = new Audio();
let cur = -1, played = 0, timer = null;
let mode = 'once';                 // once | range | all
let loopRng = false, shiftStage = 0;
let rngFrom = 0, rngTo = 4, rangeActive = false;
let grpStart = 0, grpPlayed = 0;
let stagePhase = 0, dictPhase = 0;
let ST = loadState();

const prog = document.getElementById('prog');
const finfo = document.getElementById('finfo');
const $id = id => document.getElementById(id);
const gapMs = () => parseInt($id('gap').value, 10);
const repN = () => parseInt($id('repeat').value, 10);
const grpN = () => parseInt($id('grpSize').value, 10) || 1;
const grpR = () => parseInt($id('grpRep').value, 10) || 1;
const practice = () => $id('practice').value;

/* ---------- 本地记忆 ---------- */
function blankState(){
  // 注意：这三个必须是 Set。返回普通数组会让 ST.rev.add/delete 直接抛异常，
  // 首次打开（localStorage 还没数据）时「显示原文 / 星标 / 重新遮住」会静默失效。
  return {mode:'none', rate:'1', gap:'0', rep:'1', autoRev:false, from:1, to:5,
          loop:false, grpSize:'1', grpRep:'1', prat:'manual', last:-1, fold:false,
          star:new Set(), heard:new Set(), rev:new Set()};
}
function loadState(){
  try{
    const raw = localStorage.getItem(KEY);
    if(!raw) return blankState();
    const s = Object.assign(blankState(), JSON.parse(raw));
    // 存档里是数组，这里必须还原成 Set
    s.star = new Set(s.star||[]); s.heard = new Set(s.heard||[]); s.rev = new Set(s.rev||[]);
    return s;
  }catch(e){ return blankState(); }
}
let saveTimer = null;
function save(){
  clearTimeout(saveTimer);
  saveTimer = setTimeout(()=>{
    try{
      localStorage.setItem(KEY, JSON.stringify({
        mode:MODE[mi],
        rate:$id('rate').value, gap:$id('gap').value, rep:$id('repeat').value,
        autoRev:$id('autoRev').checked, from:+($id('fromN').value||1), to:+($id('toN').value||1),
        loop:loopRng, grpSize:$id('grpSize').value, grpRep:$id('grpRep').value,
        prat:$id('practice').value, last:cur,
        fold:document.querySelector('.panel').classList.contains('folded'),
        star:[...ST.star], heard:[...ST.heard], rev:[...ST.rev]
      }));
    }catch(e){ /* file:// 下可能被禁用，忽略 */ }
  }, 120);
}

/* ---------- 显示 ---------- */
function updProg(){
  let t = cur>=0 ? ('第 '+(cur+1)+' / '+NROW+' 句') : ('共 '+NROW+' 句');
  if(mode!=='once' && rangeActive) t += ' · 连播 '+(rngFrom+1)+'–'+(rngTo+1);
  else if(mode==='all') t += ' · 全篇连播';
  const pc = Math.round(ST.heard.size/NROW*100);
  prog.innerHTML = t + ' · 已练 <b>'+ST.heard.size+'</b> / '+NROW+' ('+pc+'%)';
  finfo.textContent = '星标 '+ST.star.size+' 句 · 已练 '+ST.heard.size+' 句';
}
function mark(i){
  ROWS.forEach(r=>r.classList.remove('on'));
  if(i>=0&&ROWS[i]){
    ROWS[i].classList.add('on');
    const box=ROWS[i].getBoundingClientRect();
    window.scrollTo({top:box.top+window.scrollY-200,behavior:'smooth'});
  }
  updProg();
}
function btnOf(i){return ROWS[i]?ROWS[i].querySelector('.play'):null;}
function resetBtns(){document.querySelectorAll('.play').forEach(b=>b.textContent='▶');}
function reveal(i,on){
  if(i<0||!ROWS[i])return;
  ROWS[i].classList.toggle('rev',on);
  if(on) ST.rev.add(i); else {ST.rev.delete(i); ROWS[i].classList.remove('cn-on');}
  save();
}
function revealAll(on){
  ROWS.forEach((r,i)=>{r.classList.toggle('rev',on);r.classList.remove('cn-on');
    if(on) ST.rev.add(i); else ST.rev.delete(i);});
  save();
}
function toggleStar(i){
  const on = !ROWS[i].classList.contains('star');
  ROWS[i].classList.toggle('star',on);
  if(on) ST.star.add(i); else ST.star.delete(i);
  save(); applyFilter();
}

/* ---------- 范围 ---------- */
function paintRange(){
  ROWS.forEach((r,i)=>r.classList.toggle('inrange', rangeActive && i>=rngFrom && i<=rngTo));
}
function clampRange(keep){
  const fi=$id('fromN'), ti=$id('toN');
  let a=parseInt(fi.value,10), b=parseInt(ti.value,10);
  if(isNaN(a))a=1; if(isNaN(b))b=NROW;
  a=Math.min(NROW,Math.max(1,a)); b=Math.min(NROW,Math.max(1,b));
  if(b<a){ if(keep==='to') a=b; else b=a; }
  fi.value=a; ti.value=b; rngFrom=a-1; rngTo=b-1;
  paintRange(); updProg();
}
function useRange(keep){clampRange(keep);rangeActive=true;paintRange();updProg();save();}
function clearRange(){
  rangeActive=false; loopRng=false; shiftStage=0; mode='once';
  const lb=$id('loopRange'); lb.classList.remove('grn'); lb.textContent='↻ 循环区间';
  paintRange(); updProg(); save();
}
function setInput(id,v){$id(id).value=v;}
function sectionRange(a,b){          // 板块标题上的播放键
  setInput('fromN',a); setInput('toN',b); useRange('from');
  startChain(false);
}

/* ---------- 连播状态机 ---------- */
function playableIndices(inRange=false){
  return ROWS.map((r,i)=>({r,i})).filter(({r,i})=>!r.classList.contains('hide') &&
    (!inRange || (i>=rngFrom && i<=rngTo))).map(({i})=>i);
}
function nextIndex(){
  if(mode==='once') return -1;
  const ids=playableIndices(mode==='range');
  const pos=ids.indexOf(cur);
  if(pos<0) return ids.find(i=>i>cur) ?? -1;
  if(grpN()>1){
    const start=Math.max(0,ids.indexOf(grpStart));
    if(pos-start+1<grpN() && pos+1<ids.length) return ids[pos+1];
    grpPlayed++;
    if(grpPlayed<grpR()) return ids[start];
    grpStart=ids[pos+1] ?? -1; grpPlayed=0;
  }
  return ids[pos+1] ?? -1;
}
function play(i,keep){
  clearTimeout(timer);
  if(i<0||i>=NROW){stop();return;}
  cur=i; played=0; stagePhase=0; dictPhase=0;
  if(practice()==='stage' && keep){setMode('none');reveal(i,false);}
  if(!keep) mode='once';
  resetBtns(); mark(i); save();
  const b=btnOf(i); if(b)b.textContent='■';
  aud.src='data:audio/mpeg;base64,'+CLIPS[i];
  aud.playbackRate=parseFloat($id('rate').value);
  aud.loop=false;  // 通过 onEnded 循环，才能记录已练并保留句间间隔
  aud.onended=onEnded;
  aud.play().catch(()=>{});
  if(practice()==='dict') showDictBar(i); else hideDictBar();
}
function onEnded(){
  if(cur<0 || !ROWS[cur])return;
  played++;
  ROWS[cur].classList.add('heard'); ST.heard.add(cur); updProg(); save();
  const N=repN();
  if(N===-1 || (N>0 && played<N)){                       // 本句还要再播一遍
    timer=setTimeout(()=>{aud.currentTime=0;aud.play().catch(()=>{});},gapMs());
    return;
  }
  const bb=btnOf(cur); if(bb)bb.textContent='▶';
  if(practice()==='stage' && mode!=='once'){
    // ① 盲听结束 → 露出英文并复听一遍 ② 复听结束 → 露出中文 ③ 下一句
    document.body.classList.add('pm-stage');
    if(stagePhase===0){
      stagePhase=1; reveal(cur,true);
      timer=setTimeout(()=>{aud.currentTime=0;aud.play().catch(()=>{});},Math.max(gapMs(),600));
      return;
    }
    ROWS[cur].classList.add('cn-on'); stagePhase=0;
    timer=setTimeout(()=>nextStep(),Math.max(gapMs(),500));
    return;
  }
  if(practice()==='dict'){ showDictBar(cur); return; }
  if($id('autoRev').checked) reveal(cur,true);
  nextStep();
}
function nextStep(){
  const nx=nextIndex();
  if(nx>=0){ timer=setTimeout(()=>play(nx,true),gapMs()); return; }
  if(loopRng && mode!=='once'){          // 循环整个范围
    const first=playableIndices(mode==='range')[0];
    if(first===undefined){stop();return;}
    grpStart=first; grpPlayed=0;
    timer=setTimeout(()=>play(first,true),Math.max(gapMs(),350));
    return;
  }
  mode='once'; updProg();
}
function stop(){
  clearTimeout(timer); aud.pause(); resetBtns();
  ROWS.forEach(r=>r.classList.remove('on'));
  cur=-1; mode='once'; stagePhase=0; updProg(); save(); hideDictBar();
}
function togglePlay(){
  if(cur<0){const first=playableIndices()[0];if(first!==undefined)play(first);return;}
  if(!aud.paused){aud.pause();const b=btnOf(cur);if(b)b.textContent='▶';return;}
  if(aud.currentTime>0.05&&aud.currentTime<aud.duration-0.05){aud.play().catch(()=>{});return;}
  play(cur);
}
function step(d){
  const ids=playableIndices();
  if(!ids.length){stop();return;}
  const pos=ids.indexOf(cur);
  const n=cur<0 ? ids[0] : pos>=0 ? ids[Math.max(0,Math.min(ids.length-1,pos+d))] :
    (d>0 ? ids.find(i=>i>cur) ?? ids.at(-1) : ids.findLast(i=>i<cur) ?? ids[0]);
  play(n);
}
function startChain(loop){
  useRange();
  if($id('scope').value==='all'){mode='all'; setInput('fromN',1); setInput('toN',NROW); useRange('from');}
  else mode='range';
  loopRng=!!loop;
  const lb=$id('loopRange');
  lb.classList.toggle('grn',loopRng);
  lb.textContent = loopRng ? '↻ 循环区间（开）' : '↻ 循环区间';
  const first=playableIndices(true)[0];
  if(first===undefined){stop();flash($id('playRange'),'没有可播放的句子');return;}
  grpStart=first; grpPlayed=0;
  play(first,true);
  save();
}

/* ---------- 听写 ---------- */
function hideDictBar(){$id('dictBar').classList.remove('on');}
function showDictBar(i){
  const bar=$id('dictBar');
  bar.classList.add('on');
  $id('dictHead').textContent='听写第 '+(i+1)+' 句 · 已播放 '+played+' 遍';
  $id('dictRes').innerHTML='';
  const box=$id('dictIn'); box.value=''; box.dataset.i=i;
  box.focus({preventScroll:true});
}
function tok(s){return s.toLowerCase().replace(/[^a-z0-9'\\u4e00-\\u9fa5 ]/g,' ')
  .split(/\\s+/).filter(Boolean);}
function diffAns(a,b){                       // a: 原文, b: 用户
  const A=tok(a), B=tok(b);
  const n=A.length, m=B.length;
  const dp=Array.from({length:n+1},()=>new Array(m+1).fill(0));
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)
    dp[i][j]= A[i]===B[j] ? dp[i+1][j+1]+1 : Math.max(dp[i+1][j],dp[i][j+1]);
  const out=[]; let i=0,j=0, right=0;
  while(i<n&&j<m){
    if(A[i]===B[j]){out.push('<span class="ok">'+A[i]+'</span>');i++;j++;right++;}
    else if(dp[i+1][j]>=dp[i][j+1]){out.push('<span class="miss">'+A[i]+'</span>');i++;}
    else {out.push('<span class="bad">'+B[j]+'</span>');j++;}
  }
  while(i<n){out.push('<span class="miss">'+A[i++]+'</span>');}
  while(j<m){out.push('<span class="bad">'+B[j++]+'</span>');}
  const score=Math.round(right/Math.max(n,m,1)*100);
  return {html:out.join(' '), score:score, right:right, total:n};
}
function dictSubmit(){
  if(cur<0)return;
  const mine=$id('dictIn').value;
  const truth=ROWS[cur].dataset.t||'';
  const r=diffAns(truth,mine);
  $id('dictRes').innerHTML='<div>正确率 <b>'+r.score+'%</b>（原文匹配 '+r.right+'/'+r.total+' 词）· 删除线为你写错的，橙色底线为漏听的词</div><div>'+r.html+'</div>';
  reveal(cur,true);
  $id('dictHint').textContent='按回车进入下一句，或点「跳过看下句」';
}

/* ---------- 导出 ---------- */
function b64ToBytes(b64){
  const bin=atob(b64); const u=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
  return u;
}
function stripID3(u){                        // 合并时去掉重复的 ID3 头
  if(u.length>10 && u[0]===0x49 && u[1]===0x44 && u[2]===0x33){
    const size=((u[6]&0x7f)<<21)|((u[7]&0x7f)<<14)|((u[8]&0x7f)<<7)|(u[9]&0x7f);
    return u.subarray(10+size);
  }
  return u;
}
function mergeRange(){
  if(!rangeActive) return null;
  const parts=[]; let total=0;
  for(let i=rngFrom;i<=rngTo;i++){
    const u=stripID3(b64ToBytes(CLIPS[i])); total+=u.length; parts.push(u);
  }
  const out=new Uint8Array(total); let p=0;
  parts.forEach(u=>{out.set(u,p);p+=u.length;});
  return out;
}
function download(blob,name){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download=name; document.body.appendChild(a); a.click();
  setTimeout(()=>{URL.revokeObjectURL(url);a.remove();},2000);
}
let CRCT=null;
function crc32(u){
  if(!CRCT){CRCT=new Int32Array(256);
    for(let n=0;n<256;n++){let c=n;
      for(let k=0;k<8;k++)c = c&1 ? 0xEDB88320^(c>>>1) : c>>>1;
      CRCT[n]=c;}}
  let c=-1;
  for(let i=0;i<u.length;i++)c=(c>>>8)^CRCT[(c^u[i])&0xFF];
  return (c^-1)>>>0;
}
function zipFiles(files){                    // files: [{name, data:Uint8Array}]
  const enc=new TextEncoder();
  const chunks=[], central=[]; let off=0;
  files.forEach(f=>{
    const nm=enc.encode(f.name), crc=crc32(f.data);
    const lh=new Uint8Array(30+nm.length);
    const dv=new DataView(lh.buffer);
    dv.setUint32(0,0x04034b50,true); dv.setUint16(4,20,true); dv.setUint16(6,0x0800,true);
    dv.setUint16(8,0,true); dv.setUint16(10,0,true); dv.setUint16(12,0,true);
    dv.setUint32(14,crc,true); dv.setUint32(18,f.data.length,true); dv.setUint32(22,f.data.length,true);
    dv.setUint16(26,nm.length,true); dv.setUint16(28,0,true);
    lh.set(nm,30);
    chunks.push(lh,f.data);
    const ch=new Uint8Array(46+nm.length);
    const cv=new DataView(ch.buffer);
    cv.setUint32(0,0x02014b50,true); cv.setUint16(4,20,true); cv.setUint16(6,20,true);
    cv.setUint16(8,0x0800,true); cv.setUint16(10,0,true); cv.setUint16(12,0,true);
    cv.setUint16(14,0,true); cv.setUint32(16,crc,true);
    cv.setUint32(20,f.data.length,true); cv.setUint32(24,f.data.length,true);
    cv.setUint16(28,nm.length,true); cv.setUint32(42,off,true);
    ch.set(nm,46);
    central.push(ch);
    off += lh.length + f.data.length;
  });
  const cdSize=central.reduce((s,c)=>s+c.length,0);
  const eocd=new Uint8Array(22); const ev=new DataView(eocd.buffer);
  ev.setUint32(0,0x06054b50,true); ev.setUint16(8,files.length,true);
  ev.setUint16(10,files.length,true); ev.setUint32(12,cdSize,true); ev.setUint32(16,off,true);
  return new Blob([...chunks,...central,eocd],{type:'application/zip'});
}
const pad=n=>String(n).padStart(3,'0');
const FILE_BASE=Array.from(document.title,c=>[47,92,58,42,63,34,60,62,124].includes(c.charCodeAt(0))?'_':c).join('').trim()||'逐句精听';
const escapeHTML=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function exportZip(){
  const files=[];
  const rows=[];
  ROWS.forEach((r,i)=>{
    const en=(r.querySelector('.en')||{}).textContent||'';
    const cne=(r.querySelector('.cn')||{}).textContent||'';
    const sec=r.closest('.grp').querySelector('h2').dataset.sec||'';
    const spk=(r.querySelector('.bd')||{}).textContent||'';
    const fn=KEY+'_'+pad(i+1)+'.mp3';
    files.push({name:fn,data:stripID3(b64ToBytes(CLIPS[i]))});
    rows.push([KEY+'_'+pad(i+1),'[sound:'+fn+']',escapeHTML(en)+(cne?'<br>'+escapeHTML(cne):''),en,cne,sec,spk]);
  });
  const csv='\\uFEFF#separator:Comma\\r\\n#html:true\\r\\n#columns:序号,Audio,Back,English,中文,板块,说话人\\r\\n'+rows.map(r=>r.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\\r\\n');
  files.push({name:'README-Anki-import.txt',data:new TextEncoder().encode(
    '1) 解压 ZIP，将 MP3 复制到当前 Anki profile 的 collection.media 文件夹。\\r\\n'+
    '2) 在 Anki 中导入 anki_cards.csv，选用 Basic（基础）笔记类型。\\r\\n'+
    '3) 字段映射：Audio → Front（正面），Back → Back（背面）；其余列忽略。\\r\\n'+
    '4) 保留“允许字段包含 HTML”；声音字段使用 Anki 原生 [sound:文件名]。\\r\\n'+
    '5) 先预览一张卡，确认声音和中英文显示正确。\\r\\n')});
  files.push({name:'anki_cards.csv',data:new TextEncoder().encode(csv)});
  download(zipFiles(files),'listening-anki-pack.zip');
  flash($id('dlZip'),'已导出');
}
function exportRange(){
  const m=mergeRange();
  if(!m){flash($id('dlRange'),'先选范围');return;}
  if(m.length>25e6){flash($id('dlRange'),'范围太大');return;}
  download(new Blob([m],{type:'audio/mpeg'}),
           FILE_BASE+'-'+pad(rngFrom+1)+'-'+pad(rngTo+1)+'.mp3');
  flash($id('dlRange'),'已保存');
}
function exportTxt(){
  const lines=[];
  ROWS.forEach((r,i)=>{
    const en=(r.querySelector('.en')||{}).textContent||'';
    const cne=(r.querySelector('.cn')||{}).textContent||'';
    const sec=r.closest('.grp').querySelector('h2').dataset.sec||'';
    if(!r.previousElementSibling) lines.push('', '【'+sec+'】');
    lines.push(pad(i+1)+'. '+en+(cne?('     '+cne):''));
  });
  download(new Blob([lines.join('\\n')],{type:'text/plain;charset=utf-8'}),
           FILE_BASE+'-中英对照.txt');
  flash($id('dlTxt'),'已保存');
}
function applyFilter(){
  const f=$id('filter').value;
  ROWS.forEach((r,i)=>{
    let show=true;
    if(f==='star') show=ST.star.has(i);
    else if(f==='todo') show=!ST.heard.has(i);
    else if(f==='done') show=ST.heard.has(i);
    r.classList.toggle('hide',!show);
  });
  document.querySelectorAll('.grp').forEach(g=>{
    const vis=Array.from(g.querySelectorAll('tr.row')).some(r=>!r.classList.contains('hide'));
    g.style.display = vis ? '' : 'none';
  });
  updProg();
}
function flash(btn,txt){
  if(!btn)return;
  const old=btn.textContent;
  btn.textContent=txt; btn.classList.add('ok');
  setTimeout(()=>{btn.textContent=old;btn.classList.remove('ok');},900);
}
function starRange(){
  if(!rangeActive){flash($id('starAll'),'先选范围');return;}
  for(let i=rngFrom;i<=rngTo;i++){ROWS[i].classList.add('star');ST.star.add(i);}
  save(); applyFilter(); flash($id('starAll'),'已星标');
}

/* ---------- 模式 ---------- */
const MODE=['none','cn','all'];
let mi=Math.max(0,MODE.indexOf(ST.mode||'none'));
function setMode(m){
  mi=Math.max(0,MODE.indexOf(m));
  MODE.forEach(x=>document.body.classList.remove('m-'+x));
  document.body.classList.add('m-'+MODE[mi]);
  document.querySelectorAll('#modes button').forEach((b,k)=>b.classList.toggle('on',k===mi));
  save();
}
document.querySelectorAll('#modes button').forEach(b=>b.onclick=()=>setMode(b.dataset.m));

/* ---------- 还原上一次的学习状态 ---------- */
(function restore(){
  const s=ST;
  setMode(s.mode||'none');
  $id('rate').value=s.rate; $id('gap').value=s.gap; $id('repeat').value=s.rep;
  $id('autoRev').checked=!!s.autoRev;
  $id('grpSize').value=s.grpSize; $id('grpRep').value=s.grpRep;
  $id('practice').value=s.prat;
  document.body.classList.toggle('pm-stage',s.prat==='stage');
  setInput('fromN',s.from); setInput('toN',s.to); useRange('from');
  loopRng=!!s.loop; rangeActive=false; paintRange();
  const lb=$id('loopRange'); lb.classList.toggle('grn',loopRng);
  lb.textContent = loopRng ? '↻ 循环区间（开）' : '↻ 循环区间';
  s.star.forEach(i=>{if(ROWS[i])ROWS[i].classList.add('star');});
  s.heard.forEach(i=>{if(ROWS[i])ROWS[i].classList.add('heard');});
  s.rev.forEach(i=>{if(ROWS[i])ROWS[i].classList.add('rev');});
  if(s.fold){
    document.querySelector('.panel').classList.add('folded');
    $id('fold').innerHTML='展开面板 &#9660;';
  }
  document.querySelectorAll('.grp').forEach(g=>{
    const rs=g.querySelectorAll('tr.row');
    if(!rs.length)return;
    const a=+rs[0].dataset.i+1, b=+rs[rs.length-1].dataset.i+1;
    const btn=g.querySelector('.secplay');
    if(btn){btn.dataset.a=a;btn.dataset.b=b;
      btn.title='连播第 '+a+'–'+b+' 句';
      btn.onclick=()=>sectionRange(a,b);}
  });
  document.querySelectorAll('.secplay2').forEach(b=>{
    b.onclick=()=>sectionRange(+b.dataset.a,+b.dataset.b);
  });
  applyFilter();
  updProg();
})();

/* ---------- 交互 ---------- */
document.getElementById('showHere').onclick=e=>{
  if(!document.body.classList.contains('m-none')) setMode('none');
  let i=cur;
  if(i<0){
    let best=0,bd=Infinity;
    ROWS.forEach((r,k)=>{
      if(r.classList.contains('hide'))return;
      const d=Math.abs((r.getBoundingClientRect().top||0)-200);
      if(d<bd){bd=d;best=k;}
    });
    i=best;
  }
  if(document.body.classList.contains('pm-stage')) ROWS[i].classList.add('cn-on');
  cur=i; reveal(i,true); mark(i); flash(e.target,'已显示');
};
document.getElementById('resetVeil').onclick=e=>{
  setMode('none'); revealAll(false); flash(e.target,'已全部遮住');
};
document.addEventListener('click',e=>{
  const st=e.target.closest('.st');
  if(st){toggleStar(+st.closest('tr.row').dataset.i);return;}
  if(e.shiftKey){
    const sr=e.target.closest('tr.row');
    if(sr){
      e.preventDefault();
      const i=+sr.dataset.i;
      if(shiftStage===0){setInput('fromN',i+1);setInput('toN',i+1);shiftStage=1;}
      else {setInput('toN',i+1);shiftStage=0;}
      useRange(shiftStage===0?'to':'from');
      const s=window.getSelection(); if(s)s.removeAllRanges();
      return;
    }
  }
  const v=e.target.closest('.veil');
  if(v){const i=+v.closest('tr.row').dataset.i;reveal(i,true);
    if(document.body.classList.contains('pm-stage'))ROWS[i].classList.add('cn-on');return;}
  const p=e.target.closest('.pin');
  if(p){reveal(+p.closest('tr.row').dataset.i,false);return;}
  const b=e.target.closest('.play');
  if(b){const i=+b.closest('tr.row').dataset.i;
    if(i===cur&&!aud.paused){aud.pause();b.textContent='▶';return;}
    play(i);return;}
  const tr=e.target.closest('tr.row');
  if(tr){const i=+tr.dataset.i;
    if(i===cur&&!aud.paused){aud.pause();const bb=btnOf(i);if(bb)bb.textContent='▶';return;}
    play(i);}
});
$id('playBtn').onclick=togglePlay;
$id('prevBtn').onclick=()=>step(-1);
$id('nextBtn').onclick=()=>step(1);
$id('stopBtn').onclick=stop;
$id('playRange').onclick=()=>startChain(false);
$id('loopRange').onclick=()=>startChain(!loopRng);
$id('setFrom').onclick=()=>{
  if(cur<0){flash($id('setFrom'),'先播一句');return;}
  setInput('fromN',cur+1); useRange('from');};
$id('setTo').onclick=()=>{
  if(cur<0){flash($id('setTo'),'先播一句');return;}
  setInput('toN',cur+1); useRange('to');};
$id('clearRange').onclick=clearRange;
$id('fromN').addEventListener('change',()=>useRange('from'));
$id('toN').addEventListener('change',()=>useRange('to'));
$id('scope').addEventListener('change',e=>{
  if(e.target.value==='all'){setInput('fromN',1);setInput('toN',NROW);useRange('from');}
});
$id('grpSize').addEventListener('change',save);
$id('grpRep').addEventListener('change',save);
$id('practice').addEventListener('change',e=>{
  document.body.classList.toggle('pm-stage',e.target.value==='stage');
  if(e.target.value!=='dict') hideDictBar(); else if(cur>=0) showDictBar(cur);
  save();
});
$id('rate').addEventListener('change',e=>{aud.playbackRate=parseFloat(e.target.value);save();});
$id('gap').addEventListener('change',save);
$id('repeat').addEventListener('change',()=>{if(cur>=0)play(cur);save();});
$id('autoRev').addEventListener('change',save);
$id('filter').addEventListener('change',applyFilter);
$id('starAll').onclick=starRange;
$id('wipe').onclick=()=>{
  if(!confirm('清空所有学习记录（星标、已练、揭开状态）？')) return;
  ST=blankState();
  try{localStorage.removeItem(KEY);}catch(e){}
  ROWS.forEach(r=>{r.classList.remove('star','heard','rev','cn-on');});
  applyFilter(); flash($id('wipe'),'已清空');
};
$id('fold').onclick=e=>{
  const p=document.querySelector('.panel');
  const f=p.classList.toggle('folded');
  e.target.innerHTML = f ? '展开面板 &#9660;' : '收起面板 &#9650;';
  save();
};
$id('dlRange').onclick=exportRange;
$id('dlZip').onclick=exportZip;
$id('dlTxt').onclick=exportTxt;
$id('dictOk').onclick=dictSubmit;
$id('dictSkip').onclick=()=>{step(1);};
$id('dictTip').onclick=()=>{
  if(cur<0)return;
  const result=document.createElement('div');
  result.innerHTML=diffAns(ROWS[cur].dataset.t||'',$id('dictIn').value).html;
  const next=result.querySelector('.miss')?.textContent;
  if(next){$id('dictIn').value=($id('dictIn').value+' '+next).trim();}
};
$id('dictIn').addEventListener('keydown',e=>{
  if(e.key!=='Enter'||e.shiftKey)return;
  e.preventDefault();
  if($id('dictRes').innerHTML) step(1); else dictSubmit();
});
document.addEventListener('keydown',e=>{
  const t=e.target.tagName;
  if(t==='SELECT'||t==='INPUT'||t==='TEXTAREA')return;
  const k=e.key;
  if(k==='ArrowDown'){e.preventDefault();step(1);}
  else if(k==='ArrowUp'){e.preventDefault();step(-1);}
  else if(k===' '){e.preventDefault();togglePlay();}
  else if(k==='h'||k==='H'){setMode(MODE[(mi+1)%3]);}
  else if(k==='s'||k==='S'){reveal(cur,true);}
  else if(k==='f'||k==='F'){if(cur>=0)toggleStar(cur);}
  else if(k==='r'||k==='R'){startChain(loopRng);}
  else if(k==='Escape'){stop();}
});
</script></body></html>
"""
