"""Build the offline, single-file preview from the publishable HTML pages."""
from pathlib import Path
from base64 import b64encode
import re
import json

root = Path(__file__).resolve().parent.parent

def prepare(source, page_name):
    source = re.sub(r'href="([a-z]+)\.html"', lambda m: f'href="#page-{m[1]}"', source)
    source = re.sub(r'href="#([\w-]+)"', lambda m: m[0] if m[1].startswith('page-') else f'href="#page-{page_name}:{m[1]}"', source)
    def embed_image(match):
        data = b64encode((root / match[1]).read_bytes()).decode()
        return f'src="data:image/svg+xml;base64,{data}"'
    return re.sub(r'src="(assets/[^\"]+\.svg)"', embed_image, source)

pages = {}
for path in sorted(root.glob('*.html')):
    if path.name == 'preview.html':
        continue
    source = prepare(path.read_text(), path.stem)
    pages[path.stem] = {
        'main': re.search(r'<main id="main">(.*?)</main>', source, re.S)[1],
        'title': re.search(r'<title>(.*?)</title>', source, re.S)[1],
    }

source = prepare((root / 'index.html').read_text(), 'index')
# Shared shell anchors stay on the current page.
source = source.replace('href="#page-index:main"', 'href="#main"')
source = source.replace('href="#page-index:top"', 'href="#top"')
source = source.replace('<link rel="stylesheet" href="assets/style.css">', '<style>' + (root / 'assets/style.css').read_text() + '</style>')
source = source.replace('<script src="assets/site.js" defer></script>', '')
favicon = b64encode((root / 'assets/mark.svg').read_bytes()).decode()
source = re.sub(r'<link rel="icon"[^>]*>', f'<link rel="icon" href="data:image/svg+xml;base64,{favicon}" type="image/svg+xml">', source)
router = r'''
const pages = PAGE_DATA;
let currentPage = null;
let pageTransition = null;
function scrollToDestination(anchor, reset) {
  if (anchor) {
    document.getElementById(anchor)?.scrollIntoView();
  } else if (reset) {
    window.scrollTo({top: 0, behavior: 'instant'});
    const heading = document.querySelector('#main h1');
    if (heading) {
      heading.setAttribute('tabindex', '-1');
      heading.focus({preventScroll: true});
    }
  }
}
function showPage(allowTransition = true) {
  const match = location.hash.match(/^#page-([a-z]+)(?::([\w-]+))?$/);
  const name = match ? match[1] : (location.hash ? currentPage || 'index' : 'index');
  const anchor = match ? match[2] : location.hash.slice(1);
  if (!pages[name]) return;
  if (currentPage === name) {
    scrollToDestination(anchor, !anchor);
    return;
  }
  const update = () => {
    document.querySelector('#main').innerHTML = pages[name].main;
    document.title = pages[name].title;
    currentPage = name;
    document.querySelectorAll('#navigation a').forEach(link => {
      if (link.getAttribute('href') === '#page-' + name) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    scrollToDestination(anchor, Boolean(match) || allowTransition);
    window.dispatchEvent(new Event('kuromugi:pagechange'));
    return Promise.all(Array.from(document.querySelectorAll('#main img')).map(image =>
      typeof image.decode === 'function' ? image.decode().catch(() => {}) : Promise.resolve()
    ));
  };
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  pageTransition?.skipTransition();
  if (allowTransition && !reducedMotion && typeof document.startViewTransition === 'function') {
    pageTransition = document.startViewTransition(update);
    pageTransition.ready.catch(() => {});
    pageTransition.finished.catch(() => {});
  } else {
    update();
  }
}
window.addEventListener('hashchange', () => showPage());
showPage(false);
'''.replace('PAGE_DATA', json.dumps(pages, ensure_ascii=False).replace('</', r'<\/'))
source = source.replace('</body>', '<script>' + router + (root / 'assets/site.js').read_text() + '</script></body>')
output = root / 'preview.html'
output.write_text(source)
output.chmod(0o644)
print(f'{output}: {output.stat().st_size:,} bytes')
