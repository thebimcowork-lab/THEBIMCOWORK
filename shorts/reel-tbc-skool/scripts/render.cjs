// Renderiza reel.html cuadro a cuadro en Chromium (Playwright) y codifica con ffmpeg.
//
//   node scripts/render.cjs out.mp4              -> video sin audio + .cache/cues.json
//   node scripts/render.cjs --stills 1.5,6,14    -> PNG de revision en .cache/stills/
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const root = path.resolve(__dirname, '..');
const cache = path.join(root, '.cache');
const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const out = stillsArg ? null : (args[0] || path.join(cache, 'video.mp4'));

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(__dirname, 'reel.html')).href);
  await page.evaluate(() => document.fonts.ready);
  const fontsOk = await page.evaluate(() =>
    ['900 100px Inter', '700 30px Inter', '500 26px JBM'].every(f => document.fonts.check(f)));
  if (!fontsOk) throw new Error('No cargaron las tipografias (Inter / JetBrains Mono)');
  const { cues, T, FPS } = await page.evaluate(() => window.CUES);
  fs.mkdirSync(cache, { recursive: true });
  fs.writeFileSync(path.join(cache, 'cues.json'), JSON.stringify({ cues, T, FPS }, null, 1));

  const axoDir = path.join(cache, 'axo');
  const axo = fs.existsSync(axoDir) ? fs.readdirSync(axoDir).filter(f => f.endsWith('.png')).sort() : [];
  const frameAt = async t => {
    let src = null;
    if (axo.length && t >= T.axo - 0.2) {
      const i = Math.min(axo.length - 1, Math.max(0, Math.floor((t - T.axo) * FPS)));
      src = pathToFileURL(path.join(axoDir, axo[i])).href;
    }
    await page.evaluate(async ({ t, src }) => {
      const img = document.getElementById('axoImg');
      if (src && img.src !== src) { img.src = src; await img.decode(); }
      window.renderAt(t);
    }, { t, src });
    return page.screenshot({ type: 'png' });
  };

  if (stillsArg) {
    const dir = path.join(cache, 'stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const t of stillsArg.split(',').map(Number)) {
      fs.writeFileSync(path.join(dir, `t_${t.toFixed(2)}.png`), await frameAt(t));
    }
  } else {
    const n = Math.round(T.end * FPS);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS),
      '-c:v', 'png', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
      '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let k = 0; k < n; k++) {
      const buf = await frameAt(k / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log(`OK ${out} · ${n} frames @ ${FPS} fps`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
