const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const [root, modulePath, executable] = process.argv.slice(2);
  if (process.version !== 'v26.8.1') throw new Error('ExpectedNode26_8_1');
  if (require(path.join(modulePath, 'package.json')).version !== '1.64.0') throw new Error('ExpectedPlaywright1_64_0');
  const { chromium } = require(modulePath);
  const plan = JSON.parse(fs.readFileSync(path.join(root, 'plan.json')));
  const browser = await chromium.launch({ executablePath: executable, chromiumSandbox: true });
  try {
    const context = await browser.newContext({ javaScriptEnabled: false });
    await context.setOffline(true);
    const page = await context.newPage();
    // The probe uses file URLs and executes only this trusted driver, not EPUB scripts.
    await page.route('**/*', route => route.request().resourceType() === 'script' ? route.abort() : route.continue());
    const rows = [];
    for (const width of plan.widths) {
      await page.setViewportSize({ width, height: 900 });
      for (const chapter of plan.chapters) {
        await page.goto(pathToFileURL(path.join(root, chapter)).href);
        const metrics = await page.evaluate(async () => {
          await document.fonts.ready;
          await Promise.all(Array.from(document.images, image => image.decode()));
          const categories = { pre: 'pre', table: 'table', image: 'img', heading: 'h1,h2,h3,h4,h5,h6', figure: 'figure,div.figure' };
          const elements = {};
          for (const [kind, selector] of Object.entries(categories)) {
            elements[kind] = Array.from(document.querySelectorAll(selector), (element, index) => {
              const rect = element.getBoundingClientRect();
              const style = getComputedStyle(element);
              return { index, left: rect.left, right: rect.right, scroll: element.scrollWidth,
                client: element.clientWidth, white_space: style.whiteSpace, wrap: style.overflowWrap };
            });
          }
          return { viewport: innerWidth, scroll: document.documentElement.scrollWidth, elements };
        });
        rows.push({ chapter, width, ...metrics });
      }
    }
    process.stdout.write(JSON.stringify({ rows, node: process.version, playwright: '1.64.0', browser: browser.version() }) + '\n');
  } finally { await browser.close(); }
}
main().catch(error => { process.stderr.write(JSON.stringify({ error: error.message }) + '\n'); process.exitCode = 1; });
