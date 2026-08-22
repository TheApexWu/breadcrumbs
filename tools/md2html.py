#!/usr/bin/env python3
"""md -> styled self-contained HTML. usage: md2html.py in.md out.html "Title" """
import html,re,sys
src=open(sys.argv[1]).read(); title=sys.argv[3] if len(sys.argv)>3 else "BREADCRUMBS"
lines=src.split('\n'); out=[]; i=0
def inl(t):
    t=html.escape(t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'`(.+?)`',r'<code>\1</code>',t)
    t=re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',r'<em>\1</em>',t)
    return t
while i<len(lines):
    l=lines[i]
    if re.match(r'^```',l):
        i+=1; buf=[]
        while i<len(lines) and not re.match(r'^```',lines[i]): buf.append(html.escape(lines[i])); i+=1
        out.append('<pre><code>'+'\n'.join(buf)+'</code></pre>'); i+=1; continue
    if l.strip().startswith('|') and i+1<len(lines) and re.match(r'^\s*\|[\s:|-]+\|\s*$',lines[i+1]):
        hdr=[c.strip() for c in l.strip().strip('|').split('|')]; i+=2; body=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            body.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i+=1
        t='<table><thead><tr>'+''.join(f'<th>{inl(c)}</th>' for c in hdr)+'</tr></thead><tbody>'
        for r in body: t+='<tr>'+''.join(f'<td>{inl(c)}</td>' for c in r)+'</tr>'
        out.append(t+'</tbody></table>'); continue
    m=re.match(r'^(#{1,6})\s+(.*)',l)
    if m: out.append(f'<h{len(m.group(1))}>{inl(m.group(2))}</h{len(m.group(1))}>'); i+=1; continue
    if re.match(r'^---+\s*$',l): out.append('<hr>'); i+=1; continue
    if l.strip().startswith('>'):
        buf=[]
        while i<len(lines) and lines[i].strip().startswith('>'): buf.append(inl(lines[i].strip()[1:].strip())); i+=1
        out.append('<blockquote>'+'<br>'.join(buf)+'</blockquote>'); continue
    if re.match(r'^\s*[-*]\s+',l):
        buf=[]
        while i<len(lines) and re.match(r'^\s*[-*]\s+',lines[i]): buf.append('<li>'+inl(re.sub(r'^\s*[-*]\s+','',lines[i]))+'</li>'); i+=1
        out.append('<ul>'+''.join(buf)+'</ul>'); continue
    if re.match(r'^\s*\d+\.\s+',l):
        buf=[]
        while i<len(lines) and re.match(r'^\s*\d+\.\s+',lines[i]): buf.append('<li>'+inl(re.sub(r'^\s*\d+\.\s+','',lines[i]))+'</li>'); i+=1
        out.append('<ol>'+''.join(buf)+'</ol>'); continue
    if l.strip()=='': i+=1; continue
    out.append('<p>'+inl(l)+'</p>'); i+=1
css="""<style>@page{margin:1.6cm}
body{font-family:-apple-system,Helvetica,Arial,sans-serif;max-width:820px;margin:32px auto;padding:0 26px;color:#1a1f2b;line-height:1.55;font-size:14.5px}
h1{font-size:27px;border-bottom:3px solid #e2564a;padding-bottom:8px;margin-top:6px;letter-spacing:-.3px}
h2{font-size:20px;margin-top:30px;color:#0b2b45;border-bottom:1px solid #dde3ec;padding-bottom:4px}
h3{font-size:16px;margin-top:20px;color:#12324f} h4{font-size:14px;margin-top:14px;color:#334}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:12.8px}
th,td{border:1px solid #ccd4df;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#0b2b45;color:#fff;font-weight:600} tr:nth-child(even) td{background:#f4f7fb}
blockquote{border-left:4px solid #e2a54a;background:#fff8ec;margin:12px 0;padding:9px 15px;color:#5a4a20;border-radius:0 5px 5px 0}
code{background:#eef1f6;padding:1.5px 5px;border-radius:4px;font-size:12.5px;font-family:ui-monospace,Menlo,monospace;color:#b23b30}
pre{background:#0f1626;color:#d8e0ee;padding:13px 16px;border-radius:7px;overflow-x:auto;font-size:12px} pre code{background:none;color:inherit;padding:0}
hr{border:none;border-top:1px solid #dde3ec;margin:24px 0} strong{color:#0b2b45}
ul,ol{margin:8px 0;padding-left:24px} li{margin:3px 0} a{color:#1668c4}</style>"""
open(sys.argv[2],'w').write(f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>{css}</head><body>{chr(10).join(out)}</body></html>')
print("wrote",sys.argv[2])
