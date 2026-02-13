"""Component Assembler — generates novel apps from description analysis.

When no stored template matches the user's description, this module
analyses the text for:
  1. UI components needed  (editor, canvas, list, card, picker, etc.)
  2. Functional verbs       (generate, edit, track, convert, flip, roll, etc.)
  3. Subject nouns           (text, color, password, dice, card, etc.)

It then composes a working single-page HTML app by selecting and
combining pre-built UI component fragments.
"""

import re
from typing import Dict, List, Tuple

# Design system for category-aware theming
try:
    from design_system import get_category_css
    HAS_DESIGN_SYSTEM = True
except ImportError:
    HAS_DESIGN_SYSTEM = False

# =====================================================================
# Component catalogue — each component is a dict with:
#   id, css, body_html, js, tags (for matching)
# =====================================================================

def _component_editor(subject: str, label: str) -> dict:
    """Textarea-based editor with preview (markdown, notes, text, etc.)."""
    return {
        "id": "editor",
        "css": """.editor-wrap{display:grid;grid-template-columns:1fr 1fr;gap:16px;min-height:400px}
.editor-pane textarea{width:100%;height:100%;min-height:380px;resize:vertical;font-family:'Courier New',monospace;font-size:14px;padding:12px;border:1px solid #ddd;border-radius:8px}
.editor-pane textarea:focus{outline:none;border-color:#ff7a59}
.preview-pane{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;overflow-y:auto;min-height:380px}
.toolbar{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.toolbar button{padding:6px 12px;font-size:13px;border-radius:6px;background:#f0f0f0;border:none;cursor:pointer;font-weight:600}
.toolbar button:hover{background:#ff7a59;color:#fff}
@media(max-width:640px){.editor-wrap{grid-template-columns:1fr}}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="toolbar">
        <button onclick="wrap('**','**')"><strong>B</strong></button>
        <button onclick="wrap('*','*')"><em>I</em></button>
        <button onclick="insertAt('\\n- ')">List</button>
        <button onclick="insertAt('\\n# ')">H1</button>
        <button onclick="insertAt('\\n## ')">H2</button>
        <button onclick="copyText()">Copy</button>
        <button onclick="clearEditor()">Clear</button>
        <button onclick="saveLocal()">Save</button>
    </div>
    <div class="editor-wrap">
        <div class="editor-pane">
            <textarea id="editor" oninput="updatePreview()" placeholder="Start writing here...">{{}}</textarea>
        </div>
        <div class="preview-pane" id="preview"><p style="color:#aaa">Preview appears here...</p></div>
    </div>
</div>""",

        "js": """function updatePreview(){var t=document.getElementById('editor').value;
var h=t.replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>').replace(/^# (.+)$/gm,'<h1>$1</h1>')
.replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>').replace(/\\*(.+?)\\*/g,'<em>$1</em>')
.replace(/^- (.+)$/gm,'<li>$1</li>').replace(/(<li>.*<\\/li>)/gs,'<ul>$1</ul>')
.replace(/`(.+?)`/g,'<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px">$1</code>')
.replace(/\\n/g,'<br>');
document.getElementById('preview').innerHTML=h||'<p style="color:#aaa">Preview appears here...</p>';}
function wrap(before,after){var e=document.getElementById('editor');var s=e.selectionStart,end=e.selectionEnd;
var sel=e.value.substring(s,end)||'text';e.value=e.value.substring(0,s)+before+sel+after+e.value.substring(end);
e.focus();updatePreview();}
function insertAt(txt){var e=document.getElementById('editor');var s=e.selectionStart;
e.value=e.value.substring(0,s)+txt+e.value.substring(s);e.focus();updatePreview();}
function copyText(){navigator.clipboard.writeText(document.getElementById('editor').value);alert('Copied!');}
function clearEditor(){if(confirm('Clear all content?')){document.getElementById('editor').value='';updatePreview();}}
function saveLocal(){localStorage.setItem('editor_content',document.getElementById('editor').value);alert('Saved!');}
(function(){var saved=localStorage.getItem('editor_content');if(saved){document.getElementById('editor').value=saved;updatePreview();}})();""",
    }


def _component_canvas(subject: str, label: str) -> dict:
    """Drawing / whiteboard canvas with basic tools."""
    return {
        "id": "canvas",
        "css": """.canvas-wrap{text-align:center}
canvas{border:2px solid #ddd;border-radius:8px;cursor:crosshair;background:#fff;touch-action:none;max-width:100%}
.toolbar{display:flex;gap:8px;justify-content:center;margin:12px 0;flex-wrap:wrap;align-items:center}
.toolbar label{font-size:13px;font-weight:600;color:#555}
.color-btn{width:30px;height:30px;border-radius:50%;border:2px solid #ddd;cursor:pointer}
.color-btn.active{border-color:#333;transform:scale(1.15)}""",

        "body": f"""<div class="card canvas-wrap">
    <h2>{label}</h2>
    <div class="toolbar">
        <label>Color:</label>
        <input type="color" id="color" value="#333333" style="width:36px;height:30px;padding:0;border:none;cursor:pointer">
        <label>Size:</label>
        <input type="range" id="size" min="1" max="30" value="4" style="width:100px">
        <button class="btn-secondary" onclick="setEraser()">Eraser</button>
        <button class="btn-secondary" onclick="clearCanvas()">Clear</button>
        <button class="btn-primary" onclick="saveCanvas()">Save PNG</button>
    </div>
    <canvas id="canvas" width="600" height="420"></canvas>
</div>""",

        "js": """var canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
var drawing=false,eraser=false;ctx.lineCap='round';ctx.lineJoin='round';
function getPos(e){var r=canvas.getBoundingClientRect();
var t=e.touches?e.touches[0]:e;return{x:t.clientX-r.left,y:t.clientY-r.top};}
function startDraw(e){drawing=true;ctx.beginPath();var p=getPos(e);ctx.moveTo(p.x,p.y);e.preventDefault();}
function draw(e){if(!drawing)return;var p=getPos(e);
ctx.strokeStyle=eraser?'#ffffff':document.getElementById('color').value;
ctx.lineWidth=document.getElementById('size').value*(eraser?3:1);
ctx.lineTo(p.x,p.y);ctx.stroke();e.preventDefault();}
function stopDraw(){drawing=false;}
canvas.addEventListener('mousedown',startDraw);canvas.addEventListener('mousemove',draw);
canvas.addEventListener('mouseup',stopDraw);canvas.addEventListener('mouseleave',stopDraw);
canvas.addEventListener('touchstart',startDraw);canvas.addEventListener('touchmove',draw);
canvas.addEventListener('touchend',stopDraw);
function setEraser(){eraser=!eraser;event.target.textContent=eraser?'Pen':'Eraser';}
function clearCanvas(){ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);}
function saveCanvas(){var a=document.createElement('a');a.download='drawing.png';a.href=canvas.toDataURL();a.click();}
clearCanvas();""",
    }


def _component_generator(subject: str, label: str) -> dict:
    """Random generator (password, color, name, lorem, etc.)."""
    # Detect what kind of generator
    sub = subject.lower()
    if "password" in sub or "passphrase" in sub:
        return _password_generator(label)
    elif "color" in sub or "palette" in sub or "colour" in sub:
        return _color_generator(label)
    elif "name" in sub or "username" in sub:
        return _name_generator(label)
    elif "quote" in sub or "motivation" in sub or "inspiration" in sub:
        return _quote_generator(label)
    elif "dice" in sub or "die" in sub:
        return _dice_roller(label)
    elif "coin" in sub:
        return _coin_flipper(label)
    elif "lorem" in sub or "placeholder" in sub or "text" in sub:
        return _lorem_generator(label)
    else:
        return _generic_generator(label, subject)


def _password_generator(label: str) -> dict:
    return {
        "id": "password_gen",
        "css": """.output{font-family:'Courier New',monospace;font-size:24px;background:#1a1b1e;color:#2ecc71;padding:20px;border-radius:8px;word-break:break-all;margin:16px 0;min-height:60px;display:flex;align-items:center;justify-content:center}
.settings{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin:12px 0}
.settings label{font-size:14px;display:flex;align-items:center;gap:6px}
.strength{height:6px;border-radius:3px;margin:8px 0;transition:all .3s}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="output" id="output">Click Generate</div>
    <div class="strength" id="strength"></div>
    <div class="settings">
        <label>Length: <input type="range" id="len" min="8" max="64" value="16" oninput="document.getElementById('len-val').textContent=this.value"><span id="len-val">16</span></label>
        <label><input type="checkbox" id="upper" checked> A-Z</label>
        <label><input type="checkbox" id="digits" checked> 0-9</label>
        <label><input type="checkbox" id="symbols" checked> !@#</label>
    </div>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-primary" onclick="generate()">Generate</button>
        <button class="btn-secondary" onclick="copyOutput()">Copy</button>
    </div>
</div>""",

        "js": """function generate(){var len=parseInt(document.getElementById('len').value);
var chars='abcdefghijklmnopqrstuvwxyz';
if(document.getElementById('upper').checked)chars+='ABCDEFGHIJKLMNOPQRSTUVWXYZ';
if(document.getElementById('digits').checked)chars+='0123456789';
if(document.getElementById('symbols').checked)chars+='!@#$%^&*()_+-=[]{}|;:,.<>?';
var pw='';for(var i=0;i<len;i++)pw+=chars[Math.floor(Math.random()*chars.length)];
document.getElementById('output').textContent=pw;
var s=document.getElementById('strength');
var score=len>=16?100:len>=12?75:len>=8?50:25;
s.style.width=score+'%';s.style.background=score>74?'#2ecc71':score>49?'#f1c40f':'#e74c3c';}
function copyOutput(){navigator.clipboard.writeText(document.getElementById('output').textContent);alert('Copied!');}
generate();""",
    }


def _color_generator(label: str) -> dict:
    return {
        "id": "color_gen",
        "css": """.palette{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:20px 0}
.swatch{width:90px;height:90px;border-radius:10px;cursor:pointer;position:relative;transition:transform .2s;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.swatch:hover{transform:scale(1.08)}
.swatch span{position:absolute;bottom:-22px;left:0;right:0;text-align:center;font-size:12px;font-family:monospace;color:#555}
.history{display:flex;gap:4px;flex-wrap:wrap;justify-content:center;margin-top:30px}
.history-dot{width:24px;height:24px;border-radius:50%;cursor:pointer;border:2px solid #eee}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <p style="color:#888;margin:6px 0">Click a swatch to copy its hex code</p>
    <div class="palette" id="palette"></div>
    <div style="display:flex;gap:10px;justify-content:center;margin-top:10px">
        <button class="btn-primary" onclick="generatePalette()">New Palette</button>
        <select id="mode" onchange="generatePalette()" style="width:auto;padding:8px 12px">
            <option value="random">Random</option>
            <option value="warm">Warm</option>
            <option value="cool">Cool</option>
            <option value="pastel">Pastel</option>
            <option value="mono">Monochrome</option>
        </select>
    </div>
    <div class="history" id="history"></div>
</div>""",

        "js": """var history=[];
function hsl2hex(h,s,l){s/=100;l/=100;var a=s*Math.min(l,1-l);
function f(n){var k=(n+h/30)%12;var c=l-a*Math.max(Math.min(k-3,9-k,1),-1);return Math.round(255*c).toString(16).padStart(2,'0');}
return'#'+f(0)+f(8)+f(4);}
function generatePalette(){var mode=document.getElementById('mode').value;var colors=[];
var baseH=Math.floor(Math.random()*360);
for(var i=0;i<5;i++){var h,s,l;
if(mode==='warm'){h=(baseH+i*15)%360;if(h>60&&h<180)h=Math.random()*60;s=65+Math.random()*25;l=45+Math.random()*25;}
else if(mode==='cool'){h=180+Math.random()*140;s=50+Math.random()*30;l=40+Math.random()*30;}
else if(mode==='pastel'){h=(baseH+i*72)%360;s=40+Math.random()*20;l=75+Math.random()*15;}
else if(mode==='mono'){h=baseH;s=30+Math.random()*50;l=20+i*15+Math.random()*10;}
else{h=Math.floor(Math.random()*360);s=50+Math.random()*40;l=35+Math.random()*35;}
colors.push(hsl2hex(h,s,l));}
var pal=document.getElementById('palette');pal.innerHTML='';
colors.forEach(function(c){var d=document.createElement('div');d.className='swatch';d.style.background=c;
d.innerHTML='<span>'+c+'</span>';d.onclick=function(){navigator.clipboard.writeText(c);d.innerHTML='<span>Copied!</span>';
setTimeout(function(){d.innerHTML='<span>'+c+'</span>';},1000);};pal.appendChild(d);});
colors.forEach(function(c){if(history.indexOf(c)===-1)history.push(c);});
renderHistory();}
function renderHistory(){var h=document.getElementById('history');h.innerHTML='';
history.slice(-20).forEach(function(c){var d=document.createElement('div');d.className='history-dot';d.style.background=c;
d.title=c;d.onclick=function(){navigator.clipboard.writeText(c);};h.appendChild(d);});}
generatePalette();""",
    }


def _name_generator(label: str) -> dict:
    return {
        "id": "name_gen",
        "css": """.output{font-size:32px;font-weight:700;color:#ff7a59;margin:20px 0;min-height:48px}
.list{columns:2;margin-top:16px;text-align:left;font-size:15px}
.list div{padding:4px 0;break-inside:avoid}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="output" id="output">—</div>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-primary" onclick="gen()">Generate One</button>
        <button class="btn-secondary" onclick="genBatch()">Generate 10</button>
        <button class="btn-secondary" onclick="copyOutput()">Copy</button>
    </div>
    <div class="list" id="list"></div>
</div>""",

        "js": """var adjs=["Swift","Bright","Dark","Cosmic","Iron","Silver","Neon","Wild","Frost","Shadow","Lunar","Crimson","Golden","Storm","Velvet","Crystal","Phantom","Titan","Nova","Azure"];
var nouns=["Phoenix","Falcon","Dragon","Viper","Tiger","Wolf","Raven","Ghost","Knight","Blade","Spark","Arrow","Rocket","Thunder","Eagle","Hunter","Rebel","Sage","Sentinel","Oracle"];
function makeName(){return adjs[Math.floor(Math.random()*adjs.length)]+nouns[Math.floor(Math.random()*nouns.length)]+Math.floor(Math.random()*100);}
function gen(){document.getElementById('output').textContent=makeName();}
function genBatch(){var list=document.getElementById('list');list.innerHTML='';
for(var i=0;i<10;i++){var d=document.createElement('div');d.textContent=makeName();list.appendChild(d);}}
function copyOutput(){navigator.clipboard.writeText(document.getElementById('output').textContent);}
gen();""",
    }


def _quote_generator(label: str) -> dict:
    return {
        "id": "quote_gen",
        "css": """.quote-box{background:#fff5f2;border-left:4px solid #ff7a59;padding:24px 28px;border-radius:0 8px 8px 0;margin:20px 0;text-align:left}
.quote-text{font-size:22px;font-style:italic;line-height:1.5;color:#333}
.quote-author{margin-top:12px;font-size:15px;font-weight:600;color:#888}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="quote-box">
        <div class="quote-text" id="quote">—</div>
        <div class="quote-author" id="author">—</div>
    </div>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-primary" onclick="newQuote()">New Quote</button>
        <button class="btn-secondary" onclick="copyQuote()">Copy</button>
    </div>
</div>""",

        "js": """var quotes=[
["The only way to do great work is to love what you do.","Steve Jobs"],
["Innovation distinguishes between a leader and a follower.","Steve Jobs"],
["Stay hungry, stay foolish.","Steve Jobs"],
["Life is what happens when you're busy making other plans.","John Lennon"],
["In the middle of difficulty lies opportunity.","Albert Einstein"],
["Imagination is more important than knowledge.","Albert Einstein"],
["The best way to predict the future is to invent it.","Alan Kay"],
["Simplicity is the ultimate sophistication.","Leonardo da Vinci"],
["Talk is cheap. Show me the code.","Linus Torvalds"],
["First, solve the problem. Then, write the code.","John Johnson"],
["The most dangerous phrase is: We've always done it this way.","Grace Hopper"],
["Any fool can write code a computer can understand. Good programmers write code humans can understand.","Martin Fowler"],
["It does not matter how slowly you go as long as you do not stop.","Confucius"],
["What you do today can improve all your tomorrows.","Ralph Marston"],
["Believe you can and you're halfway there.","Theodore Roosevelt"]];
function newQuote(){var q=quotes[Math.floor(Math.random()*quotes.length)];
document.getElementById('quote').textContent='"'+q[0]+'"';
document.getElementById('author').textContent='— '+q[1];}
function copyQuote(){navigator.clipboard.writeText(document.getElementById('quote').textContent+' '+document.getElementById('author').textContent);}
newQuote();""",
    }


def _dice_roller(label: str) -> dict:
    return {
        "id": "dice_roller",
        "css": """.dice-area{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin:20px 0}
.die{width:80px;height:80px;background:#fff;border:3px solid #ddd;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:700;color:#ff7a59;transition:all .3s}
.die.rolling{animation:roll .4s ease-in-out}
@keyframes roll{0%{transform:rotate(0)}25%{transform:rotate(20deg)}50%{transform:rotate(-20deg)}75%{transform:rotate(10deg)}100%{transform:rotate(0)}}
.total{font-size:28px;font-weight:700;color:#333;margin:10px 0}
.history{font-size:13px;color:#888;margin-top:16px;max-height:120px;overflow-y:auto}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div style="display:flex;gap:10px;justify-content:center;align-items:center;margin-bottom:10px">
        <label style="font-size:14px;font-weight:600">Dice:</label>
        <select id="numDice" style="width:60px"><option>1</option><option selected>2</option><option>3</option><option>4</option><option>5</option><option>6</option></select>
        <label style="font-size:14px;font-weight:600">Sides:</label>
        <select id="sides" style="width:60px"><option>4</option><option selected>6</option><option>8</option><option>10</option><option>12</option><option>20</option></select>
    </div>
    <div class="dice-area" id="dice"></div>
    <div class="total">Total: <span id="total">—</span></div>
    <button class="btn-primary" onclick="rollDice()">Roll!</button>
    <div class="history" id="hist"></div>
</div>""",

        "js": """function rollDice(){var n=parseInt(document.getElementById('numDice').value);
var s=parseInt(document.getElementById('sides').value);
var area=document.getElementById('dice');area.innerHTML='';var total=0;
for(var i=0;i<n;i++){var v=Math.floor(Math.random()*s)+1;total+=v;
var d=document.createElement('div');d.className='die rolling';d.textContent=v;area.appendChild(d);}
document.getElementById('total').textContent=total;
var hist=document.getElementById('hist');
hist.innerHTML=n+'d'+s+' = '+total+'<br>'+hist.innerHTML;
if(hist.children.length>20)hist.removeChild(hist.lastChild);}
rollDice();""",
    }


def _coin_flipper(label: str) -> dict:
    return {
        "id": "coin_flip",
        "css": """.coin{width:120px;height:120px;border-radius:50%;margin:20px auto;display:flex;align-items:center;justify-content:center;font-size:48px;font-weight:700;transition:all .3s;box-shadow:0 4px 16px rgba(0,0,0,.15)}
.coin.heads{background:linear-gradient(135deg,#f1c40f,#f39c12);color:#fff}
.coin.tails{background:linear-gradient(135deg,#bdc3c7,#95a5a6);color:#fff}
.coin.flipping{animation:flip .5s ease-in-out}
@keyframes flip{0%{transform:rotateY(0)}50%{transform:rotateY(180deg)}100%{transform:rotateY(360deg)}}
.stats{display:flex;gap:30px;justify-content:center;margin:16px 0;font-size:15px}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="coin heads" id="coin">H</div>
    <p id="result" style="font-size:20px;font-weight:600;margin:10px 0">—</p>
    <div class="stats">
        <span>Heads: <strong id="h-count">0</strong></span>
        <span>Tails: <strong id="t-count">0</strong></span>
        <span>Total: <strong id="total">0</strong></span>
    </div>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-primary" onclick="flipCoin()">Flip!</button>
        <button class="btn-secondary" onclick="resetStats()">Reset</button>
    </div>
</div>""",

        "js": """var heads=0,tails=0;
function flipCoin(){var coin=document.getElementById('coin');coin.classList.add('flipping');
setTimeout(function(){coin.classList.remove('flipping');
var isHeads=Math.random()<0.5;if(isHeads){heads++;coin.className='coin heads';coin.textContent='H';
document.getElementById('result').textContent='Heads!';document.getElementById('result').style.color='#f39c12';}
else{tails++;coin.className='coin tails';coin.textContent='T';
document.getElementById('result').textContent='Tails!';document.getElementById('result').style.color='#95a5a6';}
document.getElementById('h-count').textContent=heads;document.getElementById('t-count').textContent=tails;
document.getElementById('total').textContent=heads+tails;},300);}
function resetStats(){heads=0;tails=0;document.getElementById('h-count').textContent='0';
document.getElementById('t-count').textContent='0';document.getElementById('total').textContent='0';}""",
    }


def _lorem_generator(label: str) -> dict:
    return {
        "id": "lorem_gen",
        "css": """.output-box{background:#fafafa;border:1px solid #ddd;border-radius:8px;padding:20px;margin:16px 0;text-align:left;font-size:15px;line-height:1.7;max-height:400px;overflow-y:auto}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div style="display:flex;gap:10px;justify-content:center;align-items:center;margin-bottom:10px">
        <label style="font-size:14px;font-weight:600">Paragraphs:</label>
        <input type="number" id="count" value="3" min="1" max="20" style="width:70px">
        <button class="btn-primary" onclick="gen()">Generate</button>
        <button class="btn-secondary" onclick="copyText()">Copy</button>
    </div>
    <div class="output-box" id="output"></div>
</div>""",

        "js": """var words="lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum".split(' ');
function randSentence(){var len=8+Math.floor(Math.random()*12);var s=[];
for(var i=0;i<len;i++)s.push(words[Math.floor(Math.random()*words.length)]);
s[0]=s[0][0].toUpperCase()+s[0].slice(1);return s.join(' ')+'.';}
function randParagraph(){var sentences=3+Math.floor(Math.random()*4);
var p=[];for(var i=0;i<sentences;i++)p.push(randSentence());return p.join(' ');}
function gen(){var n=parseInt(document.getElementById('count').value)||3;
var out=document.getElementById('output');out.innerHTML='';
for(var i=0;i<n;i++){var p=document.createElement('p');p.textContent=randParagraph();p.style.marginBottom='12px';out.appendChild(p);}}
function copyText(){navigator.clipboard.writeText(document.getElementById('output').textContent);alert('Copied!');}
gen();""",
    }


def _generic_generator(label: str, subject: str) -> dict:
    """Fallback generator with customizable random output."""
    return {
        "id": "generic_gen",
        "css": """.output{font-size:28px;font-weight:700;color:#ff7a59;margin:20px 0;padding:24px;background:#fff5f2;border-radius:12px;min-height:60px}
.history{margin-top:20px;text-align:left;font-size:14px;max-height:200px;overflow-y:auto}
.history div{padding:6px 0;border-bottom:1px solid #f0f0f0}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <p style="color:#888;margin:6px 0">Generate random {subject.lower()}s</p>
    <div class="output" id="output">—</div>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-primary" onclick="generate()">Generate</button>
        <button class="btn-secondary" onclick="copyOutput()">Copy</button>
    </div>
    <div class="history" id="history"></div>
</div>""",

        "js": f"""var pool=["Alpha","Bravo","Charlie","Delta","Echo","Foxtrot","Golf","Hotel","India",
"Juliet","Kilo","Lima","Mike","November","Oscar","Papa","Quebec","Romeo","Sierra",
"Tango","Uniform","Victor","Whiskey","Xray","Yankee","Zulu"];
function generate(){{var pick=pool[Math.floor(Math.random()*pool.length)]+'-'+Math.floor(Math.random()*1000);
document.getElementById('output').textContent=pick;
var hist=document.getElementById('history');
var d=document.createElement('div');d.textContent=pick;hist.insertBefore(d,hist.firstChild);
if(hist.children.length>20)hist.removeChild(hist.lastChild);}}
function copyOutput(){{navigator.clipboard.writeText(document.getElementById('output').textContent);}}
generate();""",
    }


def _component_typing_test(label: str) -> dict:
    """Typing speed test."""
    return {
        "id": "typing_test",
        "css": """.text-display{background:#fafafa;border:1px solid #ddd;border-radius:8px;padding:20px;font-size:18px;line-height:1.8;text-align:left;margin:16px 0;min-height:100px}
.text-display span.correct{color:#2ecc71}.text-display span.wrong{color:#e74c3c;text-decoration:underline}
.text-display span.current{background:#fff3cd;border-radius:2px}
.stats{display:flex;gap:24px;justify-content:center;margin:16px 0;font-size:15px}
.stat-big{font-size:48px;font-weight:700;color:#ff7a59}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="stats">
        <span>WPM: <strong id="wpm">0</strong></span>
        <span>Accuracy: <strong id="acc">100%</strong></span>
        <span>Time: <strong id="timer">0s</strong></span>
    </div>
    <div class="text-display" id="display"></div>
    <input id="input" placeholder="Start typing here..." autofocus>
    <div style="margin-top:12px">
        <button class="btn-primary" onclick="newTest()">New Text</button>
    </div>
</div>""",

        "js": """var texts=["The quick brown fox jumps over the lazy dog near the riverbank.",
"Programming is the art of telling a computer what to do in small logical steps.",
"Every great developer you know got there by solving problems they were unqualified to solve.",
"The best error message is the one that never shows up on the screen.",
"Code is like humor. When you have to explain it, it is not that good anymore.",
"In theory there is no difference between theory and practice but in practice there is."];
var text,pos,errors,startTime,running;
function newTest(){text=texts[Math.floor(Math.random()*texts.length)];pos=0;errors=0;running=false;startTime=null;
document.getElementById('input').value='';document.getElementById('wpm').textContent='0';
document.getElementById('acc').textContent='100%';document.getElementById('timer').textContent='0s';render();}
function render(){var html='';for(var i=0;i<text.length;i++){
var cls=i<pos?(text[i]===text[i]?'correct':'wrong'):i===pos?'current':'';
html+='<span'+(cls?' class="'+cls+'"':'')+'>'+text[i]+'</span>';}
document.getElementById('display').innerHTML=html;}
document.getElementById('input').addEventListener('input',function(e){
if(!running){running=true;startTime=Date.now();tick();}
var val=e.target.value;var lastChar=val[val.length-1];
if(lastChar===text[pos]){pos++;}else{errors++;pos++;}
e.target.value='';
var elapsed=(Date.now()-startTime)/1000;var words=pos/5;
document.getElementById('wpm').textContent=elapsed>0?Math.round(words/(elapsed/60)):0;
document.getElementById('acc').textContent=Math.round(((pos-errors)/Math.max(pos,1))*100)+'%';
render();if(pos>=text.length){running=false;document.getElementById('input').placeholder='Done! Click New Text';}});
function tick(){if(!running)return;var elapsed=Math.round((Date.now()-startTime)/1000);
document.getElementById('timer').textContent=elapsed+'s';setTimeout(tick,1000);}
newTest();""",
    }


def _component_flashcard(subject: str, label: str) -> dict:
    """Flashcard study tool with flip animation."""
    return {
        "id": "flashcard",
        "css": """.flip-card{width:320px;height:200px;perspective:800px;margin:20px auto;cursor:pointer}
.flip-inner{width:100%;height:100%;transition:transform .5s;transform-style:preserve-3d;position:relative}
.flip-card.flipped .flip-inner{transform:rotateY(180deg)}
.flip-front,.flip-back{position:absolute;width:100%;height:100%;backface-visibility:hidden;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:600;padding:20px;text-align:center}
.flip-front{background:#ff7a59;color:#fff}.flip-back{background:#2ecc71;color:#fff;transform:rotateY(180deg)}
.progress{font-size:14px;color:#888;margin:10px 0}
.add-form{margin-top:16px;padding-top:16px;border-top:1px solid #eee}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <p style="color:#888;font-size:14px">Click the card to flip it</p>
    <div class="flip-card" id="card" onclick="flipCard()">
        <div class="flip-inner">
            <div class="flip-front" id="front">Question</div>
            <div class="flip-back" id="back">Answer</div>
        </div>
    </div>
    <p class="progress"><span id="pos">1</span> / <span id="total">0</span></p>
    <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn-secondary" onclick="prev()">&#9664; Prev</button>
        <button class="btn-primary" onclick="next()">Next &#9654;</button>
        <button class="btn-secondary" onclick="shuffle()">Shuffle</button>
    </div>
    <div class="add-form">
        <p style="font-size:13px;font-weight:600;color:#555;margin-bottom:8px">Add a card:</p>
        <div style="display:flex;gap:8px">
            <input id="new-front" placeholder="Front (question)">
            <input id="new-back" placeholder="Back (answer)">
            <button class="btn-primary" onclick="addCard()">Add</button>
        </div>
    </div>
</div>""",

        "js": """var cards=[{f:"What is H2O?",b:"Water"},{f:"Speed of light?",b:"~300,000 km/s"},
{f:"Largest planet?",b:"Jupiter"},{f:"Python creator?",b:"Guido van Rossum"},
{f:"Year of moon landing?",b:"1969"},{f:"Chemical symbol for Gold?",b:"Au"}];
var idx=0;
function showCard(){var c=cards[idx];document.getElementById('front').textContent=c.f;
document.getElementById('back').textContent=c.b;document.getElementById('card').classList.remove('flipped');
document.getElementById('pos').textContent=idx+1;document.getElementById('total').textContent=cards.length;}
function flipCard(){document.getElementById('card').classList.toggle('flipped');}
function next(){idx=(idx+1)%cards.length;showCard();}
function prev(){idx=(idx-1+cards.length)%cards.length;showCard();}
function shuffle(){for(var i=cards.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=cards[i];cards[i]=cards[j];cards[j]=t;}idx=0;showCard();}
function addCard(){var f=document.getElementById('new-front').value.trim();var b=document.getElementById('new-back').value.trim();
if(!f||!b){alert('Enter both front and back');return;}
cards.push({f:f,b:b});document.getElementById('new-front').value='';document.getElementById('new-back').value='';
showCard();}
try{var saved=JSON.parse(localStorage.getItem('flashcards'));if(saved&&saved.length)cards=saved;}catch(e){}
window.addEventListener('beforeunload',function(){localStorage.setItem('flashcards',JSON.stringify(cards));});
showCard();""",
    }


def _component_kanban(subject: str, label: str) -> dict:
    """Kanban / todo board with drag and drop."""
    return {
        "id": "kanban",
        "css": """.kanban{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.column{background:#f8f8f8;border-radius:10px;padding:12px;min-height:300px}
.column h3{font-size:14px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;text-align:center}
.task{background:#fff;border:1px solid #eee;border-radius:8px;padding:10px 12px;margin-bottom:8px;cursor:grab;font-size:14px;transition:all .15s;position:relative}
.task:hover{border-color:#ff7a59;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.task .del{position:absolute;top:6px;right:8px;font-size:16px;color:#ccc;cursor:pointer;background:none;border:none;padding:0}
.task .del:hover{color:#e74c3c}
.column.over{background:#fff5f2}
.add-row{display:flex;gap:8px;margin-bottom:12px}
@media(max-width:640px){.kanban{grid-template-columns:1fr}}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="add-row">
        <input id="new-task" placeholder="New task..." style="flex:1">
        <button class="btn-primary" onclick="addTask()">Add</button>
    </div>
    <div class="kanban">
        <div class="column" id="col-todo" ondragover="allowDrop(event)" ondrop="drop(event,'todo')"><h3>To Do</h3></div>
        <div class="column" id="col-doing" ondragover="allowDrop(event)" ondrop="drop(event,'doing')"><h3>In Progress</h3></div>
        <div class="column" id="col-done" ondragover="allowDrop(event)" ondrop="drop(event,'done')"><h3>Done</h3></div>
    </div>
</div>""",

        "js": """var tasks=JSON.parse(localStorage.getItem('kanban_tasks')||'[]');var nextId=tasks.length?Math.max(...tasks.map(t=>t.id))+1:1;
function save(){localStorage.setItem('kanban_tasks',JSON.stringify(tasks));}
function render(){['todo','doing','done'].forEach(function(col){
var el=document.getElementById('col-'+col);
var h=el.querySelector('h3').outerHTML;
el.innerHTML=h;
tasks.filter(t=>t.col===col).forEach(function(t){
var d=document.createElement('div');d.className='task';d.draggable=true;d.dataset.id=t.id;
d.innerHTML=t.text+'<button class="del" onclick="delTask('+t.id+')">&times;</button>';
d.addEventListener('dragstart',function(e){e.dataTransfer.setData('id',t.id);});
el.appendChild(d);});});}
function addTask(){var input=document.getElementById('new-task');var txt=input.value.trim();
if(!txt)return;tasks.push({id:nextId++,text:txt,col:'todo'});input.value='';save();render();}
function delTask(id){tasks=tasks.filter(t=>t.id!==id);save();render();}
function allowDrop(e){e.preventDefault();e.currentTarget.classList.add('over');}
document.querySelectorAll('.column').forEach(c=>{c.addEventListener('dragleave',function(){c.classList.remove('over');});});
function drop(e,col){e.preventDefault();e.currentTarget.classList.remove('over');
var id=parseInt(e.dataTransfer.getData('id'));var t=tasks.find(t=>t.id===id);if(t){t.col=col;save();render();}}
document.getElementById('new-task').addEventListener('keydown',function(e){if(e.key==='Enter')addTask();});
render();""",
    }


def _component_chat(subject: str, label: str) -> dict:
    """Simple chat interface (client-side only, localStorage)."""
    return {
        "id": "chat",
        "css": """.messages{height:360px;overflow-y:auto;padding:12px;background:#fafafa;border:1px solid #ddd;border-radius:8px;margin:12px 0}
.msg{margin-bottom:10px;display:flex;flex-direction:column}
.msg .bubble{max-width:80%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5}
.msg.me{align-items:flex-end}.msg.me .bubble{background:#ff7a59;color:#fff;border-bottom-right-radius:4px}
.msg.other{align-items:flex-start}.msg.other .bubble{background:#e9ecef;color:#333;border-bottom-left-radius:4px}
.msg .meta{font-size:11px;color:#aaa;margin-top:3px}
.chat-input{display:flex;gap:8px}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div style="display:flex;gap:8px;margin-bottom:8px">
        <input id="username" placeholder="Your name" value="User" style="width:120px">
        <button class="btn-secondary" onclick="clearChat()">Clear Chat</button>
    </div>
    <div class="messages" id="messages"></div>
    <div class="chat-input">
        <input id="msg-input" placeholder="Type a message..." style="flex:1" autofocus>
        <button class="btn-primary" onclick="sendMsg()">Send</button>
    </div>
</div>""",

        "js": """var messages=JSON.parse(localStorage.getItem('chat_messages')||'[]');
function render(){var el=document.getElementById('messages');el.innerHTML='';
messages.forEach(function(m){var d=document.createElement('div');d.className='msg me';
d.innerHTML='<div class="bubble">'+m.text+'</div><div class="meta">'+m.user+' &middot; '+m.time+'</div>';
el.appendChild(d);});el.scrollTop=el.scrollHeight;}
function sendMsg(){var input=document.getElementById('msg-input');var txt=input.value.trim();
if(!txt)return;var user=document.getElementById('username').value||'User';
var now=new Date();var time=now.getHours()+':'+String(now.getMinutes()).padStart(2,'0');
messages.push({user:user,text:txt,time:time});
localStorage.setItem('chat_messages',JSON.stringify(messages));input.value='';render();}
function clearChat(){messages=[];localStorage.removeItem('chat_messages');render();}
document.getElementById('msg-input').addEventListener('keydown',function(e){if(e.key==='Enter')sendMsg();});
render();""",
    }


def _component_pomodoro(label: str) -> dict:
    """Pomodoro timer with work/break cycles."""
    return {
        "id": "pomodoro",
        "css": """.timer-display{font-size:80px;font-weight:700;color:#ff7a59;margin:20px 0;font-variant-numeric:tabular-nums}
.mode{font-size:18px;color:#888;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
.mode.work{color:#27ae60}.mode.break{color:#3498db}
.controls{display:flex;gap:12px;justify-content:center;margin:20px 0}
.settings{margin-top:20px;padding-top:16px;border-top:1px solid #eee}
.settings label{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:14px}
.settings input[type=number]{width:60px;padding:6px;text-align:center}
.cycle-dots{display:flex;gap:6px;justify-content:center;margin:12px 0}
.dot{width:10px;height:10px;border-radius:50%;background:#ddd}.dot.done{background:#27ae60}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="mode" id="mode">Work Time</div>
    <div class="timer-display" id="timer">25:00</div>
    <div class="cycle-dots" id="dots"></div>
    <div class="controls">
        <button class="btn-primary" id="startBtn" onclick="toggle()">Start</button>
        <button class="btn-secondary" onclick="reset()">Reset</button>
        <button class="btn-secondary" onclick="skip()">Skip</button>
    </div>
    <div class="settings">
        <label>Work: <input type="number" id="workMin" value="25" min="1" max="60"> min</label>
        <label>Break: <input type="number" id="breakMin" value="5" min="1" max="30"> min</label>
        <label>Cycles: <input type="number" id="cycles" value="4" min="1" max="10"></label>
    </div>
</div>""",

        "js": """var timer,running=false,isWork=true,seconds,cycle=0,totalCycles=4;
function getWorkSec(){return parseInt(document.getElementById('workMin').value)*60||1500;}
function getBreakSec(){return parseInt(document.getElementById('breakMin').value)*60||300;}
function updateDots(){totalCycles=parseInt(document.getElementById('cycles').value)||4;
var el=document.getElementById('dots');el.innerHTML='';
for(var i=0;i<totalCycles;i++){var d=document.createElement('div');d.className='dot'+(i<cycle?' done':'');el.appendChild(d);}}
function display(){var m=Math.floor(seconds/60),s=seconds%60;
document.getElementById('timer').textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');}
function toggle(){if(running){clearInterval(timer);running=false;document.getElementById('startBtn').textContent='Start';}
else{if(!seconds)seconds=getWorkSec();timer=setInterval(tick,1000);running=true;document.getElementById('startBtn').textContent='Pause';}}
function tick(){seconds--;display();if(seconds<=0){new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+btoa(String.fromCharCode.apply(null,new Uint8Array(2000).fill(128)))).play().catch(()=>{});
if(isWork){cycle++;updateDots();if(cycle>=totalCycles){alert('Pomodoro complete!');reset();return;}}
isWork=!isWork;seconds=isWork?getWorkSec():getBreakSec();
document.getElementById('mode').textContent=isWork?'Work Time':'Break Time';
document.getElementById('mode').className='mode '+(isWork?'work':'break');}}
function reset(){clearInterval(timer);running=false;isWork=true;cycle=0;seconds=getWorkSec();
document.getElementById('startBtn').textContent='Start';
document.getElementById('mode').textContent='Work Time';document.getElementById('mode').className='mode work';
display();updateDots();}
function skip(){clearInterval(timer);running=false;if(isWork)cycle++;
isWork=!isWork;seconds=isWork?getWorkSec():getBreakSec();
document.getElementById('mode').textContent=isWork?'Work Time':'Break Time';
document.getElementById('mode').className='mode '+(isWork?'work':'break');
display();updateDots();}
reset();""",
    }


def _component_habit_tracker(label: str) -> dict:
    """Daily habit tracker with streak counting."""
    return {
        "id": "habit_tracker",
        "css": """.habits{margin:16px 0}
.habit{display:flex;align-items:center;gap:12px;padding:12px;background:#f8f8f8;border-radius:8px;margin-bottom:8px}
.habit-name{flex:1;font-weight:600}
.streak{font-size:13px;color:#888}
.streak span{color:#ff7a59;font-weight:700}
.check-btn{width:32px;height:32px;border-radius:50%;border:2px solid #ddd;background:#fff;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
.check-btn.done{background:#27ae60;border-color:#27ae60;color:#fff}
.del-btn{background:none;border:none;color:#ccc;cursor:pointer;font-size:18px;padding:4px}
.del-btn:hover{color:#e74c3c}
.add-row{display:flex;gap:8px;margin-top:16px}
.week-view{display:flex;gap:4px;margin:16px 0;justify-content:center}
.day{width:28px;height:28px;border-radius:4px;background:#f0f0f0;font-size:10px;display:flex;align-items:center;justify-content:center;color:#888}
.day.today{border:2px solid #ff7a59;font-weight:700}.day.done{background:#27ae60;color:#fff}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="week-view" id="weekView"></div>
    <div class="habits" id="habits"></div>
    <div class="add-row">
        <input id="newHabit" placeholder="New habit...">
        <button class="btn-primary" onclick="addHabit()">Add</button>
    </div>
</div>""",

        "js": """var habits=JSON.parse(localStorage.getItem('habits')||'[]');
var today=new Date().toISOString().slice(0,10);
function save(){localStorage.setItem('habits',JSON.stringify(habits));}
function renderWeek(){var el=document.getElementById('weekView');el.innerHTML='';
var names=['S','M','T','W','T','F','S'];var d=new Date();d.setDate(d.getDate()-d.getDay());
for(var i=0;i<7;i++){var day=new Date(d);day.setDate(d.getDate()+i);var ds=day.toISOString().slice(0,10);
var isToday=ds===today;var allDone=habits.length>0&&habits.every(h=>(h.done||[]).includes(ds));
var div=document.createElement('div');div.className='day'+(isToday?' today':'')+(allDone?' done':'');
div.textContent=names[i];el.appendChild(div);}}
function render(){var el=document.getElementById('habits');el.innerHTML='';
habits.forEach(function(h,i){var doneToday=(h.done||[]).includes(today);
var streak=0;var d=new Date();while((h.done||[]).includes(d.toISOString().slice(0,10))){streak++;d.setDate(d.getDate()-1);}
var div=document.createElement('div');div.className='habit';
div.innerHTML='<button class="check-btn'+(doneToday?' done':'')+'" onclick="toggleHabit('+i+')">'+(doneToday?'✓':'')+'</button>'+
'<span class="habit-name">'+h.name+'</span><span class="streak">Streak: <span>'+streak+'</span></span>'+
'<button class="del-btn" onclick="delHabit('+i+')">&times;</button>';
el.appendChild(div);});renderWeek();}
function addHabit(){var input=document.getElementById('newHabit');var name=input.value.trim();
if(!name)return;habits.push({name:name,done:[]});input.value='';save();render();}
function toggleHabit(i){var h=habits[i];h.done=h.done||[];var idx=h.done.indexOf(today);
if(idx>=0)h.done.splice(idx,1);else h.done.push(today);save();render();}
function delHabit(i){if(confirm('Delete this habit?')){habits.splice(i,1);save();render();}}
document.getElementById('newHabit').addEventListener('keydown',function(e){if(e.key==='Enter')addHabit();});
render();""",
    }


def _component_expense_tracker(label: str) -> dict:
    """Simple expense tracker with categories and totals."""
    return {
        "id": "expense_tracker",
        "css": """.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.summary-box{background:#f8f8f8;padding:12px;border-radius:8px;text-align:center}
.summary-box .label{font-size:12px;color:#888;text-transform:uppercase}
.summary-box .val{font-size:24px;font-weight:700;margin-top:4px}
.summary-box.income .val{color:#27ae60}.summary-box.expense .val{color:#e74c3c}
.entries{margin:16px 0;max-height:300px;overflow-y:auto}
.entry{display:flex;align-items:center;gap:12px;padding:10px;border-bottom:1px solid #eee}
.entry:last-child{border:none}
.entry-cat{width:10px;height:10px;border-radius:50%}
.entry-desc{flex:1}
.entry-amount{font-weight:600;font-variant-numeric:tabular-nums}
.entry-amount.income{color:#27ae60}.entry-amount.expense{color:#e74c3c}
.entry-del{background:none;border:none;color:#ccc;cursor:pointer}
.entry-del:hover{color:#e74c3c}
.add-form{display:grid;grid-template-columns:1fr 100px 120px auto;gap:8px;margin-top:16px}
.cat-legend{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;font-size:12px}
.cat-legend span{display:flex;align-items:center;gap:4px}
@media(max-width:500px){.add-form{grid-template-columns:1fr 1fr}.summary{grid-template-columns:1fr}}""",

        "body": f"""<div class="card">
    <h2>{label}</h2>
    <div class="summary">
        <div class="summary-box income"><div class="label">Income</div><div class="val" id="income">$0</div></div>
        <div class="summary-box expense"><div class="label">Expenses</div><div class="val" id="expenses">$0</div></div>
        <div class="summary-box"><div class="label">Balance</div><div class="val" id="balance">$0</div></div>
    </div>
    <div class="entries" id="entries"></div>
    <div class="add-form">
        <input id="desc" placeholder="Description">
        <input id="amount" type="number" step="0.01" placeholder="Amount">
        <select id="cat"><option value="food">🍔 Food</option><option value="transport">🚗 Transport</option>
        <option value="bills">📄 Bills</option><option value="shopping">🛒 Shopping</option>
        <option value="income">💰 Income</option><option value="other">📦 Other</option></select>
        <button class="btn-primary" onclick="addEntry()">Add</button>
    </div>
</div>""",

        "js": """var entries=JSON.parse(localStorage.getItem('expenses')||'[]');
var catColors={food:'#e67e22',transport:'#3498db',bills:'#9b59b6',shopping:'#e74c3c',income:'#27ae60',other:'#95a5a6'};
function save(){localStorage.setItem('expenses',JSON.stringify(entries));}
function render(){var el=document.getElementById('entries');el.innerHTML='';
var income=0,expense=0;entries.forEach(function(e,i){
if(e.cat==='income')income+=e.amount;else expense+=e.amount;
var div=document.createElement('div');div.className='entry';
var sign=e.cat==='income'?'+':'-';var cls=e.cat==='income'?'income':'expense';
div.innerHTML='<div class="entry-cat" style="background:'+catColors[e.cat]+'"></div>'+
'<span class="entry-desc">'+e.desc+'</span>'+
'<span class="entry-amount '+cls+'">'+sign+'$'+e.amount.toFixed(2)+'</span>'+
'<button class="entry-del" onclick="delEntry('+i+')">&times;</button>';
el.appendChild(div);});
document.getElementById('income').textContent='$'+income.toFixed(2);
document.getElementById('expenses').textContent='$'+expense.toFixed(2);
document.getElementById('balance').textContent='$'+(income-expense).toFixed(2);
document.getElementById('balance').style.color=(income-expense)>=0?'#27ae60':'#e74c3c';}
function addEntry(){var desc=document.getElementById('desc').value.trim();
var amount=parseFloat(document.getElementById('amount').value);
var cat=document.getElementById('cat').value;
if(!desc||isNaN(amount)||amount<=0){alert('Enter description and valid amount');return;}
entries.unshift({desc:desc,amount:amount,cat:cat,date:new Date().toISOString()});
document.getElementById('desc').value='';document.getElementById('amount').value='';save();render();}
function delEntry(i){entries.splice(i,1);save();render();}
render();""",
    }


# =====================================================================
# Pattern detection — what components does the description need?
# =====================================================================

def _component_game(game_type: str, label: str) -> dict:
    """Create a game component placeholder.
    
    Note: Games should normally bypass the component assembler via 
    REQUIRED_FEATURE_TEMPLATES in codegen.py and use dedicated generators.
    This provides a fallback structure if a game accidentally routes here.
    """
    return {
        "id": game_type,
        "label": label,
        "type": "game",
        "css": ".game-container{text-align:center;padding:20px}",
        "body": f'<div class="card game-container"><h2>{label}</h2><p>Loading {game_type.replace("_", " ")} game...</p><p style="color:#888;font-size:14px">If this message persists, the game generator may not be configured.</p></div>',
        "js": f"console.log('Game component stub for {game_type} - should use dedicated generator');"
    }

# (pattern_regex, component_builder_function, priority)
COMPONENT_PATTERNS: List[Tuple[str, object, int]] = [
    # Specific generators
    (r"password\s*(gen|creat|mak|random)", lambda s, l: _component_generator("password", l), 90),
    (r"color\s*(palette|gen|pick|random|creat)|palette\s*(gen|creat|mak)", lambda s, l: _component_generator("color palette", l), 90),
    (r"dice\s*(roll|throw|game)|roll\s*(dice|die)", lambda s, l: _component_generator("dice", l), 90),
    (r"coin\s*(flip|toss)|flip\s*(a\s*)?coin|toss\s*(a\s*)?coin", lambda s, l: _component_generator("coin", l), 90),
    (r"quote\s*(gen|random|daily|motiv|inspir)|random\s*quote|daily\s*quote", lambda s, l: _component_generator("quote", l), 90),
    (r"lorem\s*ipsum|placeholder\s*text|text\s*gen", lambda s, l: _component_generator("lorem", l), 90),
    (r"(user)?name\s*gen|random\s*name", lambda s, l: _component_generator("name", l), 85),
    
    # Game patterns
    (r"snake\s*game|snake\b.*game|classic\s*snake", lambda s, l: _component_game("snake", l), 92),
    (r"tetris|falling\s*blocks?|block\s*stack", lambda s, l: _component_game("tetris", l), 92),
    (r"2048|twenty.?forty.?eight|tile\s*merge|merge\s*tiles?", lambda s, l: _component_game("game_2048", l), 92),
    (r"wordle|word\s*guess|guess\s*the\s*word", lambda s, l: _component_game("wordle", l), 90),
    (r"hangman|hang\s*man", lambda s, l: _component_game("hangman", l), 90),
    (r"tic\s*tac\s*toe|noughts?\s*(and|&)\s*crosses?|x\s*(and|&)\s*o", lambda s, l: _component_game("tictactoe", l), 90),
    (r"minesweeper|mine\s*sweep|mines?\s*game|bomb\s*grid|flag\s*mines?", lambda s, l: _component_game("minesweeper", l), 90),
    (r"memory\s*(game|card|match)|matching\s*(game|card)|card\s*match", lambda s, l: _component_game("memory_game", l), 88),
    (r"sliding\s*puzzle|tile\s*puzzle|15\s*puzzle|puzzle\s*game", lambda s, l: _component_game("sliding_puzzle", l), 88),
    (r"quiz|trivia|question\s*(game|app)", lambda s, l: _component_game("quiz", l), 85),
    (r"guess\s*(the\s*)?(number|num)|number\s*guess", lambda s, l: _component_game("guess_game", l), 85),
    (r"reaction\s*(time|game|test)|reflex\s*(test|game)|simon\s*(game|says)?|grid\s*click|click\s*(the\s*)?(green|tile|target)|whack\s*a\s*mole", lambda s, l: _component_game("reaction_game", l), 85),

    # Productivity / Tracker patterns
    (r"pomodoro|focus\s*timer|work\s*timer|productivity\s*timer", lambda s, l: _component_pomodoro(l), 90),
    (r"habit\s*(track|log|app)|daily\s*habit|streak\s*(track|count)|routine\s*track", lambda s, l: _component_habit_tracker(l), 88),
    (r"expense\s*(track|log|app)|budget\s*(track|app)|money\s*track|spending\s*(track|log)|finance\s*track", lambda s, l: _component_expense_tracker(l), 88),

    # UI patterns
    (r"typing\s*(speed|test|practic)|speed\s*typ|wpm\s*test", lambda s, l: _component_typing_test(l), 88),
    (r"flashcard|study\s*card|flash\s*card|spaced\s*rep", lambda s, l: _component_flashcard(s, l), 85),
    (r"kanban|task\s*board|project\s*board|trello|scrum\s*board", lambda s, l: _component_kanban(s, l), 85),
    (r"chat\s*(room|app|interface|box)|messaging|messenger", lambda s, l: _component_chat(s, l), 85),
    (r"draw(ing)?|whiteboard|sketch|paint|canvas\s*app|doodle", lambda s, l: _component_canvas(s, l), 80),
    (r"(markdown|text|note|code)\s*(editor|writer|pad)|notepad|scratchpad|journal\s*app", lambda s, l: _component_editor(s, l), 80),

    # Generic generator fallback (must be after specific ones)
    (r"gen(erat|erator)|random(ize|izer)?|creat(e|or)|mak(e|er)", lambda s, l: _component_generator(s, l), 30),
]


def detect_components(description: str) -> List[Tuple[int, dict]]:
    """Detect which UI components are needed from a description.
    
    Returns list of (priority, component_dict) tuples, highest priority first.
    """
    desc = description.lower()
    matches: List[Tuple[int, dict]] = []

    for pattern, builder, priority in COMPONENT_PATTERNS:
        if re.search(pattern, desc):
            label = description.strip().title()
            if len(label) > 50:
                label = label[:47] + "..."
            component = builder(desc, label)
            # Avoid duplicates
            if not any(m[1]["id"] == component["id"] for m in matches):
                matches.append((priority, component))

    # Sort by priority (highest first)
    matches.sort(key=lambda x: -x[0])
    return matches


def can_assemble(description: str, min_priority: int = 0) -> bool:
    """Check if the assembler can handle this description.
    
    Args:
        min_priority: Only return True if the best match has at least this priority.
    """
    comps = detect_components(description)
    if not comps:
        return False
    return comps[0][0] >= min_priority


def assemble_html(title: str, description: str) -> str:
    """Compose a complete HTML page from detected components."""
    components = detect_components(description)
    if not components:
        return ""  # Caller should use its own fallback

    # Use the first (highest priority) component
    _, comp = components[0]

    # Use design system for base CSS if available
    if HAS_DESIGN_SYSTEM:
        base_css = get_category_css(description)
    else:
        # Fallback to original styling
        base_css = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#ff7a59;color:#fff;padding:16px 20px;text-align:center}
.navbar h1{font-size:22px;font-weight:700}
.container{max-width:700px;margin:30px auto;padding:0 16px}
.card{background:#fff;border-radius:12px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:16px;text-align:center}
button{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:600;transition:all .2s}
.btn-primary{background:#ff7a59;color:#fff}.btn-primary:hover{background:#ff6b3f;transform:translateY(-1px)}
.btn-secondary{background:#6c757d;color:#fff}.btn-secondary:hover{background:#5a6268}
input,select,textarea{padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;width:100%;margin-bottom:10px;font-family:inherit}
input:focus,textarea:focus{outline:none;border-color:#ff7a59;box-shadow:0 0 0 3px rgba(255,122,89,.15)}"""
    
    # Component-specific CSS
    component_css = comp.get("css", "")

    # Build a minimal base page with the component
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{base_css}
{component_css}
</style>
</head>
<body>
<nav class="navbar"><h1>{title}</h1></nav>
<div class="container">
{comp.get("body", "")}
</div>
<script>
{comp.get("js", "")}
</script>
</body>
</html>"""
