#!/usr/bin/env python3
"""Regenerate index.html with latest Facebook Page posts (read-only Graph API GET)."""
import requests, html, os, datetime, re
PAGE='1014332855090842'; G='https://graph.facebook.com/v21.0/'
D=os.path.dirname(os.path.abspath(__file__))
tok=open('/home/box/.fb_page_token_longlived').read().strip()
r=requests.get(G+PAGE+'/posts',params={'fields':'message,created_time,permalink_url,full_picture','limit':9,'access_token':tok},timeout=30).json()
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
    cards.append(f'''<article class="card">{img}<div class="cb"><time>{t:%d/%m/%Y %H:%M} น. (เวลาไทย)</time><h3>{html.escape(title)}</h3><p>{html.escape(body)}…</p><a href="{html.escape(p.get('permalink_url',''))}" target="_blank" rel="noopener">อ่านต่อบน Facebook / Read on Facebook →</a></div></article>''')
posts='\n'.join(cards) or '<p>ยังไม่มีโพสต์ / No posts yet.</p>'
tpl=open(f'{D}/template.html',encoding='utf-8').read()
out=tpl.replace('{{POSTS}}',posts).replace('{{UPDATED}}',datetime.datetime.now(datetime.timezone.utc).strftime('%d/%m/%Y %H:%M UTC'))
open(f'{D}/index.html','w',encoding='utf-8').write(out)
print('posts:',len(cards))
