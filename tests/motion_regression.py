"""Real-browser navigation regression checks. Serve the repo and set TEST_SITE_URL."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('TEST_SITE_URL', 'http://127.0.0.1:8082/').rstrip('/') + '/'
PAGES = ['index', 'about', 'menu', 'journal', 'information', 'reservation', 'faq', 'privacy']
TITLES = {'about': '久呂無木について', 'menu': '蕎麦と酒', 'journal': 'お知らせ', 'information': '店舗・アクセス', 'reservation': 'ご来店・ご予約', 'faq': 'よくあるご質問', 'privacy': 'プライバシーについて'}
SAMPLE = r'''() => {
 window.motionFrames = [];
 const started = performance.now();
 function record() {
   const main = document.querySelector('#main');
   const heading = document.querySelector('h1');
   if (main && heading) {
     let opacity = 1;
     for (let e = heading; e; e = e.parentElement) opacity *= Number(getComputedStyle(e).opacity);
     motionFrames.push({time: performance.now(), main: Number(getComputedStyle(main).opacity), heading: opacity, title: heading.textContent});
   }
   if (performance.now() - started < 850) requestAnimationFrame(record);
 }
 requestAnimationFrame(record);
}'''

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get('TEST_BROWSER', '/usr/bin/chromium'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    page.on('response', lambda response: errors.append(f'{response.status}: {response.url}') if response.status >= 400 else None)

    for width in [320,375,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for name in PAGES:
            assert page.goto(BASE + name + '.html').status == 200
            assert page.locator('h1').count() == 1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name,width)
            assert page.locator('#main').evaluate('(e)=>getComputedStyle(e).opacity') == '1'
        print(f'All 8 pages: {width}px layout passed', flush=True)

    for width in [375,1440]:
        page.set_viewport_size({'width':width,'height':900})
        page.goto(BASE + 'preview.html')
        page.wait_for_timeout(1200)
        for name in ['menu','about','journal','information','reservation','faq','privacy','index']:
            page.evaluate(SAMPLE)
            if width == 375:
                page.locator('.nav-toggle').click()
            page.locator(f'#navigation a[href="#page-{name}"]').click() if name in ['menu','about','journal','information','reservation'] else page.locator(f'footer a[href="#page-{name}"]').click()
            if name != 'index':
                page.wait_for_function('(t)=>document.querySelector("h1").textContent===t', arg=TITLES[name])
            else:
                page.wait_for_function('document.querySelector("h1").textContent.includes("蕎麦を手繰る")')
            page.wait_for_timeout(950)
            frames = page.evaluate('motionFrames')
            assert len(frames)>8, (name,'Too few frames')
            assert min(f['main'] for f in frames) >= .99, (name,'Main went transparent')
            assert min(f['heading'] for f in frames) >= .99, (name,'Visible heading flashed')
            assert page.locator('.reading-progress').count()==1
        print(f'Preview: 8 real clicks and per-frame opacity passed at {width}px', flush=True)

    page.set_viewport_size({'width':1440,'height':900})
    page.goto(BASE+'preview.html')
    page.locator('#navigation a[href="#page-menu"]').click()
    page.wait_for_timeout(50)
    page.locator('#navigation a[href="#page-about"]').click()
    page.wait_for_timeout(50)
    page.locator('#navigation a[href="#page-information"]').click()
    page.wait_for_timeout(750)
    assert page.locator('h1').inner_text() == TITLES['information']
    page.go_back();page.wait_for_timeout(600);assert page.locator('h1').inner_text()==TITLES['about']
    page.go_back();page.wait_for_timeout(600);assert page.locator('h1').inner_text()==TITLES['menu']
    page.go_back();page.wait_for_timeout(600);assert '蕎麦を手繰る' in page.locator('h1').inner_text()
    page.go_forward();page.wait_for_timeout(600);assert page.locator('h1').inner_text()==TITLES['menu']
    page.locator('a[href="#page-menu:dinner"]').click();page.wait_for_timeout(700)
    assert page.locator('h1').inner_text()==TITLES['menu']
    assert page.locator('#dinner').evaluate('(e)=>Math.abs(e.getBoundingClientRect().top-110)<5')
    page.reload();page.wait_for_timeout(700);assert page.locator('h1').inner_text()==TITLES['menu']
    page.locator('footer a[href="#top"]').click();page.wait_for_timeout(600);assert page.locator('h1').inner_text()==TITLES['menu']
    page.locator('.skip').focus();page.keyboard.press('Enter');page.wait_for_timeout(600);assert page.locator('h1').inner_text()==TITLES['menu']
    print('Rapid clicks, back/forward, initial-page history, anchors, anchored reload and shared shell links passed',flush=True)

    # Native HTML links: instrument every destination before its script runs.
    page.add_init_script('''window.opacityFrames=[];function sample(){const m=document.querySelector('#main');if(m)opacityFrames.push(Number(getComputedStyle(m).opacity));requestAnimationFrame(sample)}requestAnimationFrame(sample)''')
    page.goto(BASE+'index.html');page.wait_for_timeout(1200)
    for name in ['menu','about','journal','information','reservation']:
        page.locator(f'#navigation a[href="{name}.html"]').click()
        page.wait_for_url('**/'+name+'.html');page.wait_for_timeout(700)
        assert page.locator('h1').inner_text()==TITLES[name]
        assert min(page.evaluate('opacityFrames'))>=.99
    page.go_back();page.wait_for_timeout(700);assert page.locator('h1').inner_text()==TITLES['information']
    page.go_forward();page.wait_for_timeout(700);assert page.locator('h1').inner_text()==TITLES['reservation']
    print('Regular HTML navigation, per-frame visibility and back/forward passed',flush=True)

    # A browser without View Transitions must remain fully functional.
    fallback = browser.new_page(viewport={'width':375,'height':900})
    fallback.add_init_script('document.startViewTransition=undefined')
    fallback.goto(BASE+'preview.html');fallback.locator('.nav-toggle').click()
    fallback.locator('#navigation a[href="#page-menu"]').click();fallback.wait_for_timeout(600)
    assert fallback.locator('h1').inner_text()==TITLES['menu']
    assert fallback.locator('#main').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
    fallback.emulate_media(reduced_motion='reduce');fallback.reload()
    fallback.locator('.nav-toggle').click();fallback.locator('#navigation a[href="#page-about"]').click();fallback.wait_for_timeout(100)
    assert fallback.locator('h1').inner_text()==TITLES['about']
    assert fallback.evaluate('document.getAnimations().length')==0
    page.emulate_media(reduced_motion='reduce');page.goto(BASE+'preview.html')
    page.locator('#navigation a[href="#page-menu"]').click();page.wait_for_timeout(100)
    assert page.locator('h1').inner_text()==TITLES['menu'];assert page.evaluate('document.getAnimations().length')==0
    page.emulate_media(reduced_motion='no-preference');page.goto(BASE+'faq.html')
    page.locator('summary').first.click();assert page.locator('details').first.get_attribute('open') is not None
    nojs = browser.new_page(java_script_enabled=False,viewport={'width':375,'height':900})
    nojs.goto(BASE+'index.html');assert nojs.locator('#navigation').is_visible()
    nojs.locator('#navigation a[href="menu.html"]').click();nojs.wait_for_url('**/menu.html');assert nojs.locator('h1').inner_text()==TITLES['menu']
    print('View Transition fallback, reduced motion, FAQ and no-JS navigation passed',flush=True)
    assert not errors, errors
    browser.close()
print('PASS: no page errors or console errors')
