// Helpers for logged-in Xiaohongshu source capture from the browser-control runtime.
// Import this module from the Node-backed browser session and pass an already
// claimed tab. It does not bypass login or anti-scraping restrictions.

import fs from "node:fs/promises";
import path from "node:path";

function normalizeText(value) {
  return String(value ?? "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function queryTerms(query) {
  return normalizeText(query)
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

function scoreCandidate(text, terms) {
  const lower = normalizeText(text).toLowerCase();
  if (!lower || terms.length === 0) return 0;
  let score = 0;
  for (const term of terms) {
    if (lower.includes(term)) score += term.length;
  }
  if (terms.every((term) => lower.includes(term))) score += 100;
  return score;
}

async function evaluatePostLinks(tab, query, limit) {
  return await tab.playwright.evaluate(
    ({ q, max }) => {
      const clean = (value) =>
        String(value || "")
          .replace(/\u00a0/g, " ")
          .replace(/\s+/g, " ")
          .trim();
      const terms = clean(q).toLowerCase().split(/\s+/).filter(Boolean);
      const score = (text) => {
        const lower = clean(text).toLowerCase();
        if (!lower || terms.length === 0) return 0;
        let value = 0;
        for (const term of terms) {
          if (lower.includes(term)) value += term.length;
        }
        if (terms.every((term) => lower.includes(term))) value += 100;
        return value;
      };
      const seen = new Set();
      return Array.from(
        document.querySelectorAll(
          'a[href*="/user/profile/"], a[href*="/search_result/"], a[href*="/explore/"]',
        ),
      )
        .map((anchor) => ({
          text: clean(anchor.innerText || anchor.textContent),
          href: anchor.href,
        }))
        .filter((item) => item.href && item.text)
        .map((item) => ({ ...item, score: score(item.text) }))
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score || a.text.length - b.text.length)
        .filter((item) => {
          const key = `${item.href}\n${item.text}`;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .slice(0, max);
    },
    { q: query, max: limit },
    { timeoutMs: 10000 },
  );
}

async function waitForXhsPostLinks(tab, query, options = {}) {
  const deadline = Date.now() + (options.timeoutMs ?? 6000);
  let candidates = [];
  do {
    candidates = await findXhsPostLinks(tab, query, options);
    if (candidates.length > 0) return candidates;
    await tab.playwright.waitForTimeout(options.intervalMs ?? 500);
  } while (Date.now() < deadline);
  return candidates;
}

export async function findXhsPostLinks(tab, query, options = {}) {
  const limit = options.limit ?? 12;
  const candidates = await evaluatePostLinks(tab, query, limit);
  if (candidates.length > 0 || !options.fallbackTextSearch) {
    return candidates;
  }

  const terms = queryTerms(query);
  const fallback = await tab.playwright.evaluate(
    ({ max }) =>
      Array.from(document.querySelectorAll("a[href]"))
        .map((anchor) => ({
          text: String(anchor.innerText || anchor.textContent || "")
            .replace(/\u00a0/g, " ")
            .replace(/\s+/g, " ")
            .trim(),
          href: anchor.href,
        }))
        .filter((item) => item.href && item.text)
        .slice(0, max),
    { max: 300 },
    { timeoutMs: 10000 },
  );
  return fallback
    .map((item) => ({ ...item, score: scoreCandidate(item.text, terms) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.text.length - b.text.length)
    .slice(0, limit);
}

export async function searchXhs(tab, query, options = {}) {
  const source = options.source || "web_explore_feed";
  const url =
    options.url ||
    `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}`;
  if (options.force || !(await tab.url()).includes("/search_result")) {
    await tab.goto(url);
    await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 15000 }).catch(() => {});
  }
  await tab.playwright.waitForTimeout(options.delayMs ?? 900);
  return { url: await tab.url(), title: await tab.title() };
}

async function getIndicator(tab) {
  return await tab.playwright.evaluate(
    () => {
      const clean = (value) => String(value || "").trim();
      return (
        Array.from(document.querySelectorAll("div,span"))
          .map((element) => clean(element.innerText || element.textContent))
          .find((text) => /^\d+\s*\/\s*\d+$/.test(text)) || ""
      );
    },
    undefined,
    { timeoutMs: 10000 },
  );
}

function parseIndicator(indicator) {
  const match = String(indicator || "").match(/(\d+)\s*\/\s*(\d+)/);
  if (!match) return { current: 1, total: 1 };
  return { current: Number(match[1]), total: Number(match[2]) };
}

async function getArrowCenters(tab) {
  return await tab.playwright.evaluate(
    () => {
      const center = (element) => {
        if (!element) return null;
        const rect = element.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
      };
      return {
        left: center(document.querySelector(".arrow-controller.left")),
        right: center(document.querySelector(".arrow-controller.right")),
      };
    },
    undefined,
    { timeoutMs: 10000 },
  );
}

async function readActiveSlide(tab) {
  return await tab.playwright.evaluate(
    () => {
      const clean = (value) => String(value || "").trim();
      const indicator =
        Array.from(document.querySelectorAll("div,span"))
          .map((element) => clean(element.innerText || element.textContent))
          .find((text) => /^\d+\s*\/\s*\d+$/.test(text)) || "";
      const activeImage = document.querySelector(".swiper-slide-active img");
      return {
        indicator,
        url: activeImage?.currentSrc || activeImage?.src || "",
      };
    },
    undefined,
    { timeoutMs: 10000 },
  );
}

async function readPostBasics(tab) {
  return await tab.playwright.evaluate(
    () => {
      const clean = (value) =>
        String(value || "")
          .replace(/\r\n/g, "\n")
          .replace(/\u00a0/g, " ")
          .trim();
      const indicator =
        Array.from(document.querySelectorAll("div,span"))
          .map((element) => clean(element.innerText || element.textContent))
          .find((text) => /^\d+\s*\/\s*\d+$/.test(text)) || "";
      const title = clean(
        document.querySelector("#detail-title")?.innerText ||
          document.title.replace(/ - 小红书$/, ""),
      );
      const description = clean(document.querySelector("#detail-desc")?.innerText || "");
      const author = clean(
        document.querySelector(".author .username, .username, a[href*='/user/profile/']")
          ?.innerText || "",
      );
      const dateLocation = clean(
        document.querySelector(".date, .date-location")?.innerText || "",
      );
      const hashtags = Array.from(
        document.querySelectorAll("#detail-desc a, a[href*='search_result']"),
      )
        .map((anchor) => clean(anchor.innerText || anchor.textContent))
        .filter((text) => text.startsWith("#"));
      const imageCandidates = Array.from(document.images)
        .map((image) => image.currentSrc || image.src)
        .filter((url) => url && url.includes("sns-webpic"));
      return {
        platform: "xiaohongshu",
        sourceUrl: location.href,
        pageTitle: document.title,
        title,
        author,
        dateLocation,
        description,
        hashtags,
        pageIndicator: indicator,
        observedImageUrls: Array.from(new Set(imageCandidates)),
      };
    },
    undefined,
    { timeoutMs: 10000 },
  );
}

async function moveToFirstSlide(tab, clickDelayMs) {
  const initial = parseIndicator(await getIndicator(tab));
  if (initial.current <= 1) return initial;
  const arrows = await getArrowCenters(tab);
  if (!arrows.left) return initial;
  for (let i = initial.current; i > 1; i -= 1) {
    await tab.cua.click({ x: arrows.left.x, y: arrows.left.y });
    await tab.playwright.waitForTimeout(clickDelayMs);
  }
  return parseIndicator(await getIndicator(tab));
}

async function collectSlides(tab, pageCount, clickDelayMs) {
  const slides = [];
  const arrows = await getArrowCenters(tab);
  for (let index = 0; index < pageCount; index += 1) {
    slides.push(await readActiveSlide(tab));
    if (index < pageCount - 1 && arrows.right) {
      await tab.cua.click({ x: arrows.right.x, y: arrows.right.y });
      await tab.playwright.waitForTimeout(clickDelayMs);
    }
  }
  return slides.filter((slide) => slide.url);
}

export async function captureCurrentXhsPost(tab, options = {}) {
  const outputDir = options.outputDir;
  if (!outputDir) {
    throw new Error("captureCurrentXhsPost requires options.outputDir");
  }
  const clickDelayMs = options.clickDelayMs ?? 450;
  await fs.mkdir(outputDir, { recursive: true });

  const screenshot = await tab.screenshot({ fullPage: false });
  const screenshotPath = path.join(outputDir, options.screenshotName || "browser-screenshot.png");
  await fs.writeFile(screenshotPath, Buffer.from(screenshot));

  await moveToFirstSlide(tab, clickDelayMs);
  const basics = await readPostBasics(tab);
  const { total } = parseIndicator(basics.pageIndicator);
  const slides = await collectSlides(tab, total || 1, clickDelayMs);
  const finalBasics = await readPostBasics(tab);
  const capture = {
    ...basics,
    pageCount: total || slides.length,
    slides,
    observedImageUrls: Array.from(
      new Set([...(basics.observedImageUrls || []), ...(finalBasics.observedImageUrls || [])]),
    ),
    capturedAt: new Date().toISOString(),
  };

  const capturePath = path.join(outputDir, options.captureName || "capture.json");
  await fs.writeFile(capturePath, JSON.stringify(capture, null, 2), "utf8");
  return {
    capturePath,
    screenshotPath,
    title: capture.title,
    sourceUrl: capture.sourceUrl,
    pageCount: capture.pageCount,
    slideCount: capture.slides.length,
    observedImageUrlCount: capture.observedImageUrls.length,
  };
}

export async function openAndCaptureXhsPost(tab, query, options = {}) {
  if (options.searchFirst) {
    await searchXhs(tab, options.searchQuery || query, {
      source: options.searchSource,
      delayMs: options.searchDelayMs,
      force: options.forceSearch,
    });
  }
  const candidates = await waitForXhsPostLinks(tab, query, {
    limit: options.limit ?? 8,
    fallbackTextSearch: true,
    timeoutMs: options.candidateWaitMs,
  });
  if (candidates.length === 0) {
    return { found: false, candidates: [] };
  }
  const selected = candidates[options.candidateIndex ?? 0];
  await tab.goto(selected.href);
  await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 15000 }).catch(() => {});
  await tab.playwright.waitForTimeout(options.initialDelayMs ?? 700);
  const captured = await captureCurrentXhsPost(tab, options);
  return { found: true, selected, candidates, ...captured };
}
