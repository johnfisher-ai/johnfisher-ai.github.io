// Renders each card source in assets/cardsrc/<slug>.html to the 1200 × 630 card.png of the article or
// guide with that slug. Usage, from the repository root:
//   node tools/cards.mjs [slug ...]          (all cards when no slug is given)
// Needs the checks' playwright-core (cd tools/checks && npm install) and a Chromium; set CHROMIUM to its path.
import { readdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium } from './checks/node_modules/playwright-core/index.mjs';

const root = resolve(import.meta.dirname, '..');
const wanted = process.argv.slice(2);
const slugs = readdirSync(`${root}/assets/cardsrc`).filter(f => f.endsWith('.html')).map(f => f.slice(0, -5))
  .filter(s => !wanted.length || wanted.includes(s));
const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
for (const slug of slugs) {
  const folder = ['articles', 'guides'].map(d => `${root}/${d}/${slug}`).find(existsSync);
  if (!folder) { console.log(`${slug}: no article or guide folder, skipped`); continue; }
  await page.goto(`file://${root}/assets/cardsrc/${slug}.html`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() => document.documentElement.scrollHeight - 630);
  await page.screenshot({ path: `${folder}/card.png` });
  console.log(`${slug}: ${folder.replace(root + '/', '')}/card.png${overflow > 0 ? `, content overflows by ${overflow}px` : ''}`);
}
await browser.close();
