#!/usr/bin/env python3
"""Regenerate index.html with latest Facebook Page posts (read-only Graph API GET)."""
import requests, html, os, datetime, re
PAGE='1014332855090842'; G='https://graph.facebook.com/v21.0/'
D=os.path.dirname(os.path.abspath(__file__))
tok=open('/home/box/.fb_page_token_longlived').read().strip()
r=requests.get(G+PAGE+'/posts',params={'fields':'message,created_time,permalink_url,full_picture,comments.order(chronological).limit(1){message,from}','limit':9,'access_token':tok},timeout=30).json()

import re as _re
from urllib.parse import urlparse
OUTLETS={'abc.net.au':'ABC News','aljazeera.com':'Al Jazeera','news.cn':'Xinhua','straitstimes.com':'The Straits Times','nationtv.tv':'เนชั่นทีวี','matichon.co.th':'มติชน','kyodonews.net':'Kyodo News','nbcnews.com':'NBC News','cnbc.com':'CNBC','pbs.org':'PBS NewsHour','japantimes.co.jp':'The Japan Times','thaipbs.or.th':'Thai PBS','bangkokpost.com':'Bangkok Post','thairath.co.th':'ไทยรัฐ','amarintv.com':'อมรินทร์ทีวี','reuters.com':'Reuters','apnews.com':'AP','bbc.com':'BBC','khaosod.co.th':'ข่าวสด','nationthailand.com':'Nation Thailand','devdiscourse.com':'Devdiscourse'}
def outlet(u):
    h=urlparse(u).netloc.lower().removeprefix('www.')
    for k,v in OUTLETS.items():
        if h==k or h.endswith('.'+k): return v
    return h
def urls(text):
    out=[]
    for u in _re.findall(r'https?://[^\s<>"]+',text or ''):
        u=u.rstrip(').,;]')
        if u not in out: out.append(u)
    return out
_dc={}
def pubdate(u):
    if u in _dc: return _dc[u]
    d=None
    try:
        h=requests.get(u,timeout=15,headers={'User-Agent':'Mozilla/5.0'}).text
        m=_re.search(r'(?:article:published_time|datePublished|pubdate|publish-date)["\']?\s*(?:content=|:)\s*["\'](\d{4}-\d{2}-\d{2})',h)
        if m: d=m.group(1)
    except Exception: pass
    _dc[u]=d; return d
REPORT=[]
# Manually verified sources for posts whose Page comment has none (website only)
MANUAL_SOURCES={
 '122163662433250428':['https://www.thaipost.net/criminality-news/1102810/','https://mgronline.com/crime/detail/9690000106356'],
 '122163240129250428':['https://www.theguardian.com/football/2026/nov/01/liverpool-arsenal-premier-league-match-report','https://www.abc.net.au/news/2026-11-02/football-arsenal-ends-anfield-drought-liverpool-var-drama/107334968'],
 '122163099585250428':['https://www.skysports.com/football/chelsea-vs-manchester-united/report/559527','https://apnews.com/article/lisandro-martinez-red-card-man-united-chelsea-8fe3b56172637a2a2ef6d48c9acff915'],
}
OUTLETS.update({'thaipost.net':'ไทยโพสต์','mgronline.com':'MGR Online','theguardian.com':'The Guardian','skysports.com':'Sky Sports'})
from urllib.parse import quote
def share(u):
    q=quote(u,safe=''); e=html.escape(u)
    return (f'<div class="share"><a href="https://www.facebook.com/sharer/sharer.php?u={q}" target="_blank" rel="noopener">Facebook</a>'
            f'<a href="https://twitter.com/intent/tweet?url={q}" target="_blank" rel="noopener">X</a>'
            f'<a href="https://social-plugins.line.me/lineit/share?url={q}" target="_blank" rel="noopener">LINE</a>'
            f'<button type="button" data-copy="{e}">คัดลอกลิงก์</button></div>')
cards=[]
os.makedirs(f'{D}/assets/posts',exist_ok=True)
for p in r.get('data',[]):
    msg=(p.get('message') or '').strip()
    if not msg or '🔥 ด่วน!' in msg: continue
    lines=[l for l in msg.split('\n') if l.strip() and not l.strip().startswith('#')]
    title=lines[0]; body=' '.join(lines[1:])[:180]
    t=datetime.datetime.strptime(p['created_time'],'%Y-%m-%dT%H:%M:%S%z')+datetime.timedelta(hours=7)
    img=''
    if p.get('full_picture'):
        fn=f"assets/posts/{p['id'].split('_')[-1]}.jpg"
        try: open(f'{D}/{fn}','wb').write(requests.get(p['full_picture'],timeout=30).content); img=f'<img src="{fn}" alt="ภาพประกอบข่าว" loading="lazy">'
        except Exception: pass
    cm=[c for c in p.get('comments',{}).get('data',[]) if c.get('from',{}).get('id')==PAGE]
    srcs=urls(msg)+[u for u in urls(cm[0]['message'] if cm else '') if u not in urls(msg)]
    if not srcs: srcs=MANUAL_SOURCES.get(p['id'].split('_')[-1],[])
    extra=''
    if srcs:
        if len(msg)>600:
            o=outlet(srcs[0]); d=pubdate(srcs[0])
            if d: dd=datetime.date.fromisoformat(d); extra+=f'<p class="ref">อ้างอิง: {html.escape(o)}, เผยแพร่ {dd:%d/%m/%Y}</p>'
            else: extra+=f'<p class="ref">อ้างอิง: {html.escape(o)} (ไม่พบวันที่เผยแพร่ที่ตรวจสอบได้)</p>'
            REPORT.append((title[:40],'long',o,d))
        else: REPORT.append((title[:40],'short',None,None))
        extra+='<p class="src">ที่มา: '+' · '.join(f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(outlet(u))}</a>' for u in srcs)+'</p>'
        REPORT[-1]+=(len(srcs),)
    else: REPORT.append((title[:40],'none',None,None,0))
    cards.append(f'''<article class="card">{img}<div class="cb"><time>{t:%d/%m/%Y %H:%M} น. (เวลาไทย)</time><h3>{html.escape(title)}</h3><p>{html.escape(body)}…</p>{extra}<a href="{html.escape(p.get('permalink_url',''))}" target="_blank" rel="noopener">อ่านต่อบน Facebook / Read on Facebook →</a>{share(p.get('permalink_url',''))}</div></article>''')
posts='\n'.join(cards) or '<p>ยังไม่มีโพสต์ / No posts yet.</p>'
tpl=open(f'{D}/template.html',encoding='utf-8').read()
out=tpl.replace('{{POSTS}}',posts).replace('{{UPDATED}}',datetime.datetime.now(datetime.timezone.utc).strftime('%d/%m/%Y %H:%M UTC'))
open(f'{D}/index.html','w',encoding='utf-8').write(out)
open(f'{D}/sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://phraison28-sudo.github.io/thainewsonline/</loc><lastmod>'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+'</lastmod><changefreq>hourly</changefreq></url></urlset>\n')
print('posts:',len(cards))
for x in REPORT: print(x)
