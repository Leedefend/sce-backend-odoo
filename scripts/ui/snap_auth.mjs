import { chromium } from "playwright";

const BASE = process.env.BASE_URL || "http://localhost:18081";
const W = parseInt(process.env.VW || "1440", 10);
const H = parseInt(process.env.VH || "900", 10);

const shots = [
  { name: "login", url: `${BASE}/web/login` },
  { name: "signup", url: `${BASE}/web/signup` },
];

const run = async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });

  await page.addStyleTag({ content: "*{transition:none !important; animation:none !important;}" });

  for (const s of shots) {
    await page.goto(s.url, { waitUntil: "networkidle" });
    await page.waitForTimeout(400);

    await page.screenshot({ path: `artifacts/${s.name}_${W}x${H}.png`, fullPage: true });

    const card = page.locator(".sc-login").first();
    if (await card.count()) {
      await card.screenshot({ path: `artifacts/${s.name}_${W}x${H}_card.png` });
    }
  }

  await browser.close();
};

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
