from pathlib import Path
import re,json
p=Path(__file__).resolve().parent.parent
css=(p/'assets/style.css').read_text()
js=(p/'assets/site.js').read_text()
def prepare(s):
 s=re.sub(r'href="([a-z]+)\.html"',lambda m:'href="#page-'+m[1]+'"',s)
 def img(m):
  from base64 import b64encode
  data=(p/m[1]).read_bytes()
  return 'src="data:image/svg+xml;base64,'+b64encode(data).decode()+'"'
 return re.sub(r'src="(assets/[^\"]+\.svg)"',img,s)
allpages={}
for f in p.glob('*.html'):
 
 if f.name=='preview.html':continue
 s=prepare(f.read_text());allpages[f.stem]={'main':re.search(r'<main id="main">(.*?)</main>',s,re.S)[1],'title':re.search(r'<title>(.*?)</title>',s,re.S)[1]}
s=prepare((p/'index.html').read_text())
s=s.replace('<link rel="stylesheet" href="assets/style.css">','<style>'+css+'</style>')
s=s.replace('<script src="assets/site.js" defer></script>','')
s=re.sub(r'<link rel="icon"[^>]*>','',s)
script='''const pages=PAGE_DATA;
function showPage(){const match=location.hash.match(/^#page-([a-z]+)$/);const name=match?match[1]:'index';if(!pages[name])return;document.querySelector('#main').innerHTML=pages[name].main;document.title=pages[name].title;document.querySelectorAll('#navigation a').forEach(a=>{if(a.getAttribute('href')==='#page-'+name)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});if(match){window.scrollTo({top:0,behavior:'instant'});const heading=document.querySelector('#main h1');if(heading){heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});}}window.dispatchEvent(new Event('kuromugi:pagechange'));}
window.addEventListener('hashchange',()=>{if(location.hash.startsWith('#page-'))showPage();});showPage();
'''.replace('PAGE_DATA',json.dumps(allpages,ensure_ascii=False).replace('</','<\\/'))+js
s=s.replace('</body>','<script>'+script+'</script></body>')
out=p/'preview.html';out.write_text(s);out.chmod(0o644)
print(out, out.stat().st_size)
