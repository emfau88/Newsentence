import asyncio,json,base64,os
from pathlib import Path
from playwright.async_api import async_playwright
P=Path(__file__).resolve().parent.parent;S=P/'screenshots';S.mkdir(exist_ok=True)
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=os.environ.get('CHROME_EXECUTABLE'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':1440,'height':960},device_scale_factor=1)
  errors=[];console=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda e:console.append({'type':e.type,'text':e.text}) if e.type in ['warning','error'] else None)
  await page.goto('http://127.0.0.1:8080/',wait_until='domcontentloaded',timeout=60000)
  await page.wait_for_function('window.testState?.ready===true',timeout=180000)
  results=[]
  for lod in [0,1,2]:
   await page.evaluate('(n)=>window.setLOD(n)',lod)
   for name in ['overview','approach','village','seam']:
    await page.evaluate('(name)=>window.setCamera(name)',name)
    await page.screenshot(path=str(S/f'lod{lod}_{name}.png'),timeout=60000)
    data=await page.evaluate('window.capture()');(S/f'lod{lod}_{name}_3d.png').write_bytes(base64.b64decode(data.split(',')[1]))
    results.append({'lod':lod,'camera':name,**(await page.evaluate('window.testState'))});print('CAPTURE',lod,name,flush=True)
  await page.select_option('#lod','0');await page.wait_for_function('window.testState.lod===0')
  await page.click('[data-camera="village"]')
  await page.set_viewport_size({'width':390,'height':844});await page.screenshot(path=str(S/'mobile_village.png'),timeout=60000)
  (P/'browser_validation.json').write_text(json.dumps({'views':results,'page_errors':errors,'console':console,'browser':'Chrome for Testing 154 / SwiftShader software WebGL','mobile_viewport':[390,844]},indent=2));assert not errors,errors
  await browser.close()
asyncio.run(main())
