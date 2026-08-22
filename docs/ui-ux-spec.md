Reconciled against the live file at `/Users/amadeuswoo/dev/straits/globe/food3d.html` (598 lines). Where the three inputs collided on the same lines I picked one owner: **theme agent → all `body.light` CSS**, **map agent → all deck.gl layer edits**, **UX agent → the `toggleBoro` 404 patch + active-state markup**. Every map-layer "Old" snippet the map agent quoted matches the current file byte-for-byte (its line numbers run ~6 low; corrected below). The building/heat colors the UX and theme agents also proposed are dropped as superseded by the map agent's internally-consistent set.

One reconciliation you should know about: the map agent tuned its light building colors against a ground of `clearColor .86/.90/.94`, but the file's actual light `clearColor` is `[.788,.831,.871,1]` (≈ `#c9d4de`) — slightly darker/cooler. The warm-gray buildings still separate from it (warm vs cool at similar luminance), so I left `clearColor` untouched. That is the only known soft spot.

---

# 1. CSS — replace the whole `body.light` block

**Replace current lines 31–38** (the existing `body.light …` rules, ending at `#rec.armed`) with this. It is the theme agent's drop-in set, reconciled two ways: `--bg` set to `#c9d4de` to match the real `clearColor` (so a canvas-load failure doesn't flash a mismatched ground), and a `body.light #rec` base rule added back (the theme block dropped it, which would have flattened the SIMULATE hero to plain white).

```css
/* ============ SIM / DAY THEME — city-planner light mode ============ */
body.light{
  --bg:#c9d4de;      /* matches deck clearColor [.788,.831,.871] so a canvas-fail doesn't flash */
  --panel:#f5f8fb;
  --bd:#c4cfdb;
  --tx:#1d2735;
  --mut:#66717f;
  --amber:#b26a15;
  --red:#d23f30;
  --grn:#2f7d4a;
  --cyan:#1f8fa3;
}

/* classification banner */
body.light #cls{background:#e7edf3;color:#5a6675;border-color:#cdd7e1}

/* frosted panels */
body.light .panel{
  background:rgba(245,248,251,.92);
  border-color:#c4cfdb;
  box-shadow:0 1px 2px rgba(28,44,72,.10), 0 6px 20px rgba(28,44,72,.07);
}
body.light #top{box-shadow:0 1px 2px rgba(28,44,72,.08)}

/* ---------- control buttons ---------- */
body.light #ctl button{
  background:#ffffff;
  color:var(--tx);
  border-color:#c4cfdb;
}
body.light #ctl button:hover{background:#eef3f8;border-color:#9fb0c4}
body.light #ctl button .n{color:var(--mut)}
body.light #ctl button.on{
  background:#fdf1dc;
  color:#8a5412;
  border-color:#cf9236;
  box-shadow:inset 2px 0 0 #c98325;
}
body.light #ctl button.on .n{color:#a5803f}
body.light #ctl button.loading{opacity:.55}
/* SIMULATE hero: amber CTA in light (theme block dropped this; re-added) */
body.light #rec{background:#fdf1dc;color:#8a5412;border-color:#cf9236}
/* recall armed = red alarm */
body.light #rec.armed{
  background:#fbe3df;color:var(--red);border-color:#d98a80;
  box-shadow:inset 2px 0 0 var(--red);
}
/* text inputs — !important beats inline background:#070b14 on #q / #ask_q */
body.light #q, body.light #ask_q{background:#ffffff !important}
body.light #q::placeholder, body.light #ask_q::placeholder{color:#9aa4b2}

/* ---------- SENTINEL panel innards ---------- */
body.light #score .sc{border-bottom-color:#e0e7ef}
body.light #score .sc:hover{background:#eaf0f6}
body.light #alerts .al{border-bottom-color:#e0e7ef}
body.light #feed .fe .t{color:#aab4c2}

/* ---------- detail panel ---------- */
body.light #d_tab td{border-bottom-color:#e0e7ef}

/* ---------- report panel Telegram button (inline bg needs !important) ---------- */
body.light #tg{background:#fdf1dc !important}
body.light #tg:hover{background:#f8e6c6 !important}

/* ---------- floating hint ---------- */
body.light #hint{background:rgba(245,248,251,.94);border-color:#c4cfdb;color:var(--mut)}
```

This overrides every hardcoded dark hex (`#131b2e`, `#0f1626`, `#39435e`) via `body.light`-scoped rules, so **dark mode is untouched** — no change to `:root` or the base rules. No token-swap edits to lines 13/21/22/24/51/78 are needed (that was the UX agent's alternate route; dropped in favor of this self-contained block).

---

# 2. JS + markup edits (ordered, non-overlapping)

### Edit 1 — hoist stable heat ramps (fixes a per-frame texture rebuild)
`HEAT.slice(1)` allocated a new array every `frame()`, forcing `HeatmapLayer` to rebuild its color texture each tick. Hoist both ramps to module scope. **Insert immediately after line 99** (`const HEAT=[...]`):

```js
const HEAT_D=HEAT.slice(1);
const HEAT_L=[[250,238,200,0],[246,212,150],[238,178,120],[230,138,100],[222,100,84],[214,72,66]];
```

The light ramp drops the green stops (green reads as "parks/good" on a pale map) and runs cream→amber→red.

### Edit 2 — building fill reads on pale ground (line 423)
**Find:**
```js
    getFillColor:d=>{const t=Math.min(1,d.h/130),rk=d.rk||0;const n0=light?188-t*40:26+t*22,n1=light?194-t*38:32+t*24,n2=light?204-t*34:46+t*30;const k=rk*0.6,r0=light?196:150,r1=light?128:112,r2=light?110:86;return [n0+(r0-n0)*k, n1+(r1-n1)*k, n2+(r2-n2)*k];},
```
**Replace:**
```js
    getFillColor:d=>{const t=Math.min(1,d.h/130),rk=d.rk||0;
      if(light){const n0=210-t*72,n1=206-t*72,n2=199-t*70,k=rk*0.4;return [n0+(232-n0)*k,n1+(150-n1)*k,n2+(120-n2)*k];}
      const n0=26+t*22,n1=32+t*24,n2=46+t*30,k=rk*0.6,r0=150,r1=112,r2=86;return [n0+(r0-n0)*k,n1+(r1-n1)*k,n2+(r2-n2)*k];},
```
Light base is warm concrete `(210,206,199)` darkening with height; risk tint weight `0.6→0.4` toward coral `(232,150,120)` (kills the brown wash). `updateTriggers:{getFillColor:light}` on line 424 already re-runs this on toggle — leave it. Dark branch byte-identical.

### Edit 3 — heat becomes a subtle wash (lines 432–434)
**Find:**
```js
  if(showHeat)L.push(new HeatmapLayer({id:'heat',data:rests,getPosition:d=>[d.lon,d.lat],
    getWeight:d=>d.rs, radiusPixels:46, intensity:1, threshold:0.04, colorRange:HEAT.slice(1),
    aggregation:'SUM'}));
```
**Replace:**
```js
  if(showHeat)L.push(new HeatmapLayer({id:'heat',data:rests,getPosition:d=>[d.lon,d.lat],
    getWeight:d=>d.rs, radiusPixels:light?40:46, intensity:light?0.75:1, threshold:light?0.05:0.04,
    opacity:light?0.5:1, colorRange:light?HEAT_L:HEAT_D, aggregation:'SUM'}));
```
Heat is pushed before the buildings, which draw with `depthTest:true`, so extrusions occlude the wash where they stand. Dark mode is byte-for-byte the original (now via `HEAT_D`).

### Edit 4 — operator's 12 site rings, high-contrast on light (lines 470–472)
**Find:**
```js
    getLineColor:d=>eset.has(d.id)?[226,86,74,255]:[90,220,255,255],
    getFillColor:d=>eset.has(d.id)?[226,86,74,150]:[70,150,190,70],
    updateTriggers:{getLineColor:recall,getFillColor:recall,getRadius:[recall,pulse]},
```
**Replace:**
```js
    getLineColor:d=>eset.has(d.id)?[226,86,74,255]:(light?[12,112,150,255]:[90,220,255,255]),
    getFillColor:d=>eset.has(d.id)?[226,86,74,150]:(light?[38,128,168,55]:[70,150,190,70]),
    updateTriggers:{getLineColor:[recall,light],getFillColor:[recall,light],getRadius:[recall,pulse]},
```
Non-exposed stroke swaps bright cyan → deep teal `(12,112,150)`. Exposed stays red in both modes (still pops on recall). `light` added to both triggers so the toggle repaints.

### Edit 5 — operator labels: dark text + light halo (lines 475–476)
**Find:**
```js
    getColor:d=>eset.has(d.id)?[255,180,170,255]:[150,228,255,235],getPixelOffset:[0,-16],getTextAnchor:'middle',fontFamily:'monospace',
    outlineWidth:2.5,outlineColor:[3,6,12,235],fontSettings:{sdf:true},billboard:true,updateTriggers:{getColor:recall}}));
```
**Replace:**
```js
    getColor:d=>eset.has(d.id)?(light?[196,40,30,255]:[255,180,170,255]):(light?[14,78,104,255]:[150,228,255,235]),getPixelOffset:[0,-16],getTextAnchor:'middle',fontFamily:'monospace',
    outlineWidth:2.5,outlineColor:light?[246,250,253,235]:[3,6,12,235],fontSettings:{sdf:true},billboard:true,updateTriggers:{getColor:[recall,light]}}));
```

### Edit 6 — supplier hub labels, same treatment (lines 464–465)
`hubT` had no `updateTriggers` — add one or it won't repaint on toggle.
**Find:**
```js
    getColor:d=>d.class1>10?[240,150,140,235]:[150,200,210,215],getPixelOffset:[0,-14],getTextAnchor:'middle',fontFamily:'monospace',
    outlineWidth:2,outlineColor:[3,6,12,220],fontSettings:{sdf:true},billboard:true}));
```
**Replace:**
```js
    getColor:d=>d.class1>10?(light?[186,52,40,235]:[240,150,140,235]):(light?[40,92,110,230]:[150,200,210,215]),getPixelOffset:[0,-14],getTextAnchor:'middle',fontFamily:'monospace',
    outlineWidth:2,outlineColor:light?[246,250,253,225]:[3,6,12,220],fontSettings:{sdf:true},billboard:true,updateTriggers:{getColor:light}}));
```

### Edit 7 — `toggleBoro` graceful 404 (lines 494–503)
`fetch` does not reject on 404; the current `.catch` sets `tag='err'` but never reverts `blayers`/`on`, so a borough that isn't on the box spins `loading…` forever.
**Find:**
```js
function toggleBoro(key,btn){
  if(blayers[key]){ blayers[key]=false; btn.classList.remove('on'); updBld(); return; }
  if(bld[key]){ blayers[key]=true; btn.classList.add('on'); updBld(); return; }
  btn.classList.add('loading'); btn.querySelector('.n')?.remove();
  const tag=document.createElement('span');tag.className='n';tag.textContent='loading '+(BCOUNT[key]/1000|0)+'k…';btn.appendChild(tag);
  fetch('assets/'+BFILES[key]).then(r=>r.json()).then(d=>{
    bld[key]=d; tagBuildings(d); blayers[key]=true; btn.classList.remove('loading'); btn.classList.add('on');
    tag.textContent=(d.length/1000|0)+'k'; updBld();
  }).catch(e=>{btn.classList.remove('loading');tag.textContent='err';});
}
```
**Replace:**
```js
function toggleBoro(key,btn){
  if(blayers[key]){ blayers[key]=false; btn.classList.remove('on'); updBld(); return; }
  if(bld[key]){ blayers[key]=true; btn.classList.add('on'); updBld(); return; }
  btn.classList.add('loading'); btn.classList.remove('on'); btn.querySelector('.n')?.remove();
  const tag=document.createElement('span');tag.className='n';tag.textContent='loading '+(BCOUNT[key]/1000|0)+'k…';btn.appendChild(tag);
  fetch('assets/'+BFILES[key])
    .then(r=>{ if(!r.ok) throw new Error('http '+r.status); return r.json(); })
    .then(d=>{ if(!Array.isArray(d)||!d.length) throw new Error('empty');
      bld[key]=d; tagBuildings(d); blayers[key]=true;
      btn.classList.remove('loading'); btn.classList.add('on');
      tag.textContent=(d.length/1000|0)+'k'; updBld();
    })
    .catch(err=>{
      blayers[key]=false; btn.classList.remove('loading','on');
      tag.textContent='n/a on box'; btn.title='asset not deployed on GB10 ('+err.message+')';
      setTimeout(()=>{ if(!blayers[key]) tag.remove(); }, 2600);
    });
}
```
Note (matches the box's failure mode): if the box serves 404s as a `200` directory-listing HTML page, `r.ok` is true and `r.json()` throws — the catch still reverts correctly, but `err.message` reads a parse/`empty` error rather than `http 404`.

### Edit 8 — theme toggle label reports current state (line 582)
Current label logic is inverted: in light mode the button reads "☾ Dark / night" and glows, so a viewer sees a day map labelled "Dark night ON." Label the current state instead. `clearColor` left at the file's existing `.788/.831/.871`.
**Find:**
```js
document.getElementById('lite').onclick=e=>{light=!light;document.body.classList.toggle('light',light);e.target.classList.toggle('on',light);e.target.textContent=light?'\u263e Dark / night':'\u2600 Light / day';dk.setProps({parameters:{clearColor:light?[.788,.831,.871,1]:[.027,.043,.07,1]}});};
```
**Replace:**
```js
document.getElementById('lite').onclick=e=>{light=!light;document.body.classList.toggle('light',light);e.target.classList.toggle('on',light);e.target.textContent=light?'\u2600 Day':'\u263e Night';dk.setProps({parameters:{clearColor:light?[.788,.831,.871,1]:[.027,.043,.07,1]}});};
```

### Edit 9 — stop `#mysites` looking like a stuck toggle (line 59)
It's a camera action, not a layer toggle, but ships `class="on"` and nothing ever clears it.
**Find:** `<button id="mysites" class="on">◈ My 12 sites</button>`
**Replace:** `<button id="mysites">◈ My 12 sites</button>`

### Edit 10 — theme button initial label matches Edit 8 (line 60)
**Find:** `  <div class="gp"><button id="lite" class="on">☾ Dark / night</button></div>`
**Replace:** `  <div class="gp"><button id="lite" class="on">☀ Day</button></div>`
Keeps `class="on"` — `light=true` at load, so the day-indicator is correctly active.

### Edit 11 — report panel no longer buries the controls (line 78)
`#rpt` (z 5) and `#ctl` (z 4) both sit at `left:14px;top:56px`, so when a recall fires `showReport()` paints the report over the control column and the operator can't reach **CLEAR RECALL**. `#ctl` is 196px wide from x=14 (ends ~210px), so `left:224px` clears it; `#right` is far-right, both stay visible during the climax.
**Find (inside the `#rpt` style attribute):** `left:14px;top:56px;width:330px`
**Replace:** `left:224px;top:56px;width:330px`

---

# 3. Dropped / deferred

- **UX token-swap route (edit lines 13/21/22/24/51/78 to `var(--btn)`/`--inp`/`--hov`/`--hair`).** Superseded by the self-contained `body.light` block in §1, which reaches the same hairlines/inputs without touching the dark base rules. Applying both would double-cover the same selectors.
- **UX's heat (`opacity 0.30`) and building recolor (§UX #4).** Same lines as map Edits 2–3; the map agent's set wins (internally consistent, correct `updateTriggers`). Theme agent's heat/building notes likewise fold into these.
- **Full `#ctl` regroup (UX #6) — reorder LAYERS/VIEW/BOROUGHS, drop the "lazy-loaded" jargon, hero-style SIMULATE.** This is a layout redesign, not an active-state fix; it reorders wired buttons and risks breaking handlers for polish only. The two real bugs it carried (stuck `#mysites`, wrong `#lite` label) are pulled out as Edits 9–10. Defer.
- **Dark-mode `.on`/`#rec` fill tints (UX #5, CSS lines 14/17).** Out of scope by the "don't break dark mode" constraint — left dark mode's `.on` styling exactly as-is. Light mode already gets the amber wash via §1.
- **`clearColor` darkening to `[.83,.86,.90]` (UX #4 optional).** The file already sits at `.788/.831/.871` (darker than that proposal). Left unchanged; the map agent's warm buildings still separate from it.
- **Freeze `#ctl`/`#read` dragging (UX #9), `#pts` "zoom in" sublabel (UX #10), ask-box relay precheck (UX #11).** Footguns/polish, no correctness impact, none in the requested edit set. Recommend but defer.
- **Deck lighting / ambient tuning.** Single shared `LightingEffect`; lowering ambient for shading contrast would darken night mode too. Not worth the risk.

**Fragile:** the light building constants in Edit 2 are eyeball-tuned against an assumed ground; verify against the real Manhattan asset in a browser, and toggle theme twice to confirm rings/labels (Edits 4–6) actually repaint — if they stay stale, the `updateTriggers:[…,light]` additions didn't land. **Breaks first:** if the pinned deck.gl 9.0.38 build ignored `HeatmapLayer` `opacity` (it doesn't), the wash would stay opaque — fallback is baking low alpha into `HEAT_L`'s stops.