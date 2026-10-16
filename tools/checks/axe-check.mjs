// Runs axe on every page of the rendered site, at 1280 px in light mode and 375 px in dark mode,
// and reports any sideways scroll. Also runs a search and checks the results page in both modes.
// Usage: node axe-check.mjs <base-url> <docs-folder> [chromium-path]
import { readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { chromium } from 'playwright-core';
import AxeBuilder from '@axe-core/playwright';

const [base, docs, exe] = process.argv.slice(2);
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'];

function pages(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (name === 'site_libs') continue;
    if (statSync(p).isDirectory()) out.push(...pages(p));
    else if (name.endsWith('.html')) out.push(relative(docs, p).split(sep).join('/').replace(/index\.html$/, ''));
  }
  return out.sort();
}

const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const modes = [
  { name: '1280 light', viewport: { width: 1280, height: 900 }, colorScheme: 'light' },
  { name: '375 dark', viewport: { width: 375, height: 800 }, colorScheme: 'dark' },
];
let failures = 0;
for (const m of modes) {
  const ctx = await browser.newContext({ viewport: m.viewport, colorScheme: m.colorScheme });
  const page = await ctx.newPage();
  for (const p of pages(docs)) {
    await page.goto(base + p, { waitUntil: 'networkidle' });
    const res = await new AxeBuilder({ page }).withTags(TAGS).analyze();
    const sideways = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    const v = res.violations.map(x => `${x.id} (${x.nodes.length}): ${x.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | ')}`);
    if (v.length || sideways > 0) failures++;
    console.log(`${m.name} | /${p} | sideways ${sideways}px | ${v.length ? v.join('; ') : 'no violations'}`);
  }
  // Search page, with results showing
  await page.goto(base + 'search/?q=handbook', { waitUntil: 'networkidle' });
  await page.waitForSelector('.pagefind-ui__result', { timeout: 10000 }).catch(() => {});
  const res = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const results = await page.locator('.pagefind-ui__result').count();
  const v = res.violations.map(x => `${x.id} (${x.nodes.length}): ${x.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | ')}`);
  if (v.length || results === 0) failures++;
  console.log(`${m.name} | /search/?q=handbook | ${results} results | ${v.length ? v.join('; ') : 'no violations'}`);
  await ctx.close();
}
await browser.close();
console.log(failures ? `axe: ${failures} page checks failed` : 'axe: all pages pass');
process.exit(failures ? 1 : 0);
