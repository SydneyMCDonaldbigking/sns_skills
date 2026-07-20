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

function isXhsPostHref(href) {
  try {
    const url = new URL(href);
    return /(^|\.)xiaohongshu\.com$/.test(url.hostname) && /^\/explore\/[^/?#]+/.test(url.pathname);
  } catch {
    return false;
  }
}

const DEFAULT_REMIX_HINTS = [
  "\u63a8\u8350",
  "\u5408\u96c6",
  "\u6e05\u5355",
  "\u6307\u5357",
  "\u6d4b\u8bc4",
  "\u6559\u7a0b",
  "\u505a\u6cd5",
  "\u98df\u8c31",
  "\u4e07\u80fd",
  "\u51ac\u5b63",
  "\u6fb3\u6d32",
  "\u4e00\u7bc7",
  "\u597d\u7269",
  "\u907f\u96f7",
  "\u6536\u85cf",
  "\u770b\u61c2",
  "\u4e70\u4ec0\u4e48",
  "\u600e\u4e48\u9009",
];

const DEFAULT_REJECT_HINTS = [
  "\u76f4\u64ad",
  "\u5e7f\u544a",
  "\u8d5e\u52a9",
  "\u62bd\u5956",
  "\u798f\u5229",
  "\u4ee3\u8d2d",
  "\u56e2\u8d2d",
  "\u62db\u8058",
  "\u79df\u623f",
  "\u4e8c\u624b",
];

function scoreRemixCandidate(candidate, terms, options = {}) {
  const title = normalizeText(candidate.title || candidate.text);
  const text = normalizeText(`${title} ${candidate.text || ""}`);
  const lower = text.toLowerCase();
  let score = candidate.href?.includes("/explore/") ? 30 : 0;

  score += scoreCandidate(text, terms) * 2;
  if (title.length >= 8 && title.length <= 80) score += 12;
  if (candidate.hasCover) score += 10;
  if ((candidate.imageCount || 0) > 0) score += Math.min(candidate.imageCount, 3) * 4;
  if (/\d+\s*(\u79cd|\u6b3e|\u4e2a|\u4ef6|\u9053|\u5927|\u7c7b)/.test(title)) {
    score += 18;
  }

  const preferHints = options.preferHints || DEFAULT_REMIX_HINTS;
  for (const hint of preferHints) {
    if (lower.includes(String(hint).toLowerCase())) score += 10;
  }

  const rejectHints = options.rejectHints || DEFAULT_REJECT_HINTS;
  for (const hint of rejectHints) {
    if (lower.includes(String(hint).toLowerCase())) score -= 25;
  }

  if (candidate.isVideo) score -= 18;
  if (candidate.isAd) score -= 35;
  if (!title) score -= 20;
  return score;
}

function xhsMediaKey(url) {
  try {
    const segment = decodeURIComponent(new URL(url).pathname).split("/").pop() || "";
    return segment.split("!", 1)[0];
  } catch {
    return "";
  }
}

function xhsQualityRank(url) {
  if (url.includes("!nd_dft")) return 30;
  if (url.includes("!nd_prv")) return 10;
  if (url.includes("sns-webpic") && url.includes("!")) return 20;
  return 0;
}

function hasObservedUpgrade(url, observedUrls) {
  const key = xhsMediaKey(url);
  if (!key) return false;
  const currentRank = xhsQualityRank(url);
  return observedUrls.some((candidate) => {
    return xhsMediaKey(candidate) === key && xhsQualityRank(candidate) > currentRank;
  });
}

function xhsCarouselStem(key) {
  const match = String(key || "").match(/^(.*?)[0-9a-z]{3}nv[0-9a-z]+$/i);
  return match?.[1] || "";
}

function compareAscii(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function bestObservedUrlsByKey(urls) {
  const best = new Map();
  for (const url of urls || []) {
    if (!url || !url.includes("sns-webpic")) continue;
    const key = xhsMediaKey(url);
    if (!key) continue;
    const current = best.get(key);
    if (!current || xhsQualityRank(url) > xhsQualityRank(current)) {
      best.set(key, url);
    }
  }
  return best;
}

export function recoverSlidesFromObserved(slides, pageCount, observedUrls) {
  if (!pageCount || pageCount <= 1 || (slides || []).length >= pageCount) {
    return null;
  }

  const seedKeys = Array.from(
    new Set((slides || []).map((slide) => xhsMediaKey(slide.url)).filter(Boolean)),
  );
  if (seedKeys.length === 0) return null;

  const bestByKey = bestObservedUrlsByKey([
    ...(observedUrls || []),
    ...(slides || []).map((slide) => slide.url),
  ]);
  const groups = new Map();
  for (const [key, url] of bestByKey.entries()) {
    const stem = xhsCarouselStem(key);
    if (stem.length < 12) continue;
    if (!groups.has(stem)) groups.set(stem, []);
    groups.get(stem).push({ key, url });
  }

  let selected = null;
  for (const [stem, items] of groups.entries()) {
    const seedHits = seedKeys.filter((key) => key.startsWith(stem)).length;
    if (seedHits === 0 || items.length !== pageCount) continue;
    const score = seedHits * 1000 + stem.length;
    if (!selected || score > selected.score) {
      selected = { score, items };
    }
  }
  if (!selected) return null;

  return selected.items
    .slice()
    .sort((left, right) => compareAscii(left.key, right.key))
    .map((item, index) => ({
      indicator: `${index + 1}/${pageCount}`,
      url: item.url,
      source: "observed-recovered",
    }));
}

async function evaluatePostCards(tab, query, options = {}) {
  const limit = options.limit ?? 12;
  const scanLimit = options.scanLimit ?? 80;
  const minScore = options.minScore ?? 25;
  const rawCards = await tab.playwright.evaluate(
    ({ max }) => {
      const clean = (value) =>
        String(value || "")
          .replace(/\u00a0/g, " ")
          .replace(/\s+/g, " ")
          .trim();
      const mediaUrl = (image) => image?.currentSrc || image?.src || "";
      const nearestCard = (anchor) => {
        let node = anchor;
        for (let depth = 0; node && depth < 7; depth += 1, node = node.parentElement) {
          const text = clean(node.innerText || node.textContent);
          const imageCount = node.querySelectorAll("img").length;
          if (imageCount > 0 && text.length <= 260) return node;
        }
        return anchor;
      };
      const seen = new Set();
      const cards = [];
      for (const anchor of Array.from(document.querySelectorAll('a[href*="/explore/"]'))) {
        const href = anchor.href;
        if (!href || seen.has(href)) continue;
        seen.add(href);
        const card = nearestCard(anchor);
        const imageUrls = Array.from(card.querySelectorAll("img"))
          .map((image) => mediaUrl(image))
          .filter(Boolean);
        const anchorText = clean(anchor.innerText || anchor.textContent);
        const cardText = clean(card.innerText || card.textContent);
        const title =
          clean(
            card.querySelector(
              "[class*='title'], [class*='desc'], .note-title, .title span, span",
            )?.innerText,
          ) ||
          anchorText ||
          cardText;
        const markerText = `${card.className || ""} ${cardText}`.toLowerCase();
        cards.push({
          href,
          title,
          text: cardText || anchorText || title,
          imageCount: imageUrls.length,
          hasCover: imageUrls.length > 0,
          isVideo: /video|play|\u89c6\u9891/.test(markerText),
          isAd: /\u5e7f\u544a|\u8d5e\u52a9|sponsor|\u63a8\u5e7f/.test(markerText),
        });
        if (cards.length >= max) break;
      }
      return cards;
    },
    { max: scanLimit },
    { timeoutMs: 10000 },
  );
  const terms = queryTerms(query);
  return rawCards
    .map((item) => ({
      ...item,
      score: scoreRemixCandidate(item, terms, {
        preferHints: options.preferHints,
        rejectHints: options.rejectHints,
      }),
    }))
    .filter((item) => item.score >= minScore)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return normalizeText(a.title).length - normalizeText(b.title).length;
    })
    .slice(0, limit);
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
        document.querySelectorAll('a[href*="/explore/"]'),
      )
        .map((anchor) => ({
          text: clean(anchor.innerText || anchor.textContent),
          href: anchor.href,
        }))
        .filter((item) => item.href && item.text && /^\/explore\/[^/?#]+/.test(new URL(item.href).pathname))
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
  const cardCandidates = await evaluatePostCards(tab, query, {
    limit,
    scanLimit: options.scanLimit,
    minScore: options.minScore,
    preferHints: options.preferHints,
    rejectHints: options.rejectHints,
  });
  if (cardCandidates.length > 0) {
    return cardCandidates;
  }

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
    .filter((item) => item.score > 0 && isXhsPostHref(item.href))
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

async function waitForActiveSlideReady(tab, timeoutMs = 1500) {
  const deadline = Date.now() + timeoutMs;
  let slide = await readActiveSlide(tab);
  while (!slide.url && Date.now() < deadline) {
    await tab.playwright.waitForTimeout(100);
    slide = await readActiveSlide(tab);
  }
  return slide;
}

async function waitForIndicatorChange(tab, previousIndicator, timeoutMs = 1500) {
  const deadline = Date.now() + timeoutMs;
  let current = previousIndicator;
  while (Date.now() < deadline) {
    await tab.playwright.waitForTimeout(100);
    current = await getIndicator(tab);
    if (current && current !== previousIndicator) return current;
  }
  return current;
}

async function collectSlidesFromDom(tab, pageCount) {
  return await tab.playwright.evaluate(
    ({ total }) => {
      const mediaKey = (url) => {
        try {
          const segment = decodeURIComponent(new URL(url).pathname).split("/").pop() || "";
          return segment.split("!", 1)[0];
        } catch {
          return url;
        }
      };
      const slideNodes = Array.from(
        document.querySelectorAll(
          ".xhs-slider-container .swiper-slide, .note-slider .swiper-slide, .swiper-slide",
        ),
      );
      const originalSlides = slideNodes.filter((slide) => {
        return !String(slide.className || "").includes("swiper-slide-duplicate");
      });
      const candidates = originalSlides.length ? originalSlides : slideNodes;
      const seen = new Set();
      const slides = [];
      for (const slide of candidates) {
        const image = slide.querySelector("img");
        const url = image?.currentSrc || image?.src || "";
        if (!url || !url.includes("sns-webpic")) continue;
        const key = mediaKey(url);
        if (seen.has(key)) continue;
        seen.add(key);
        slides.push({
          indicator: `${slides.length + 1}/${total || candidates.length}`,
          url,
          naturalWidth: image?.naturalWidth || 0,
          naturalHeight: image?.naturalHeight || 0,
          source: "dom",
        });
        if (total && slides.length >= total) break;
      }
      return slides;
    },
    { total: pageCount },
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
          document.title.replace(/\s-\s.+$/, ""),
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
  const seenIndicators = new Set();
  const arrows = await getArrowCenters(tab);
  for (let attempt = 0; attempt < pageCount + 2; attempt += 1) {
    const slide = await waitForActiveSlideReady(tab, Math.max(1500, clickDelayMs * 5));
    const key = slide.indicator || `${slides.length + 1}/${pageCount}`;
    if (slide.url && !seenIndicators.has(key)) {
      slides.push(slide);
      seenIndicators.add(key);
    }
    if (slides.length >= pageCount || !arrows.right) break;
    const before = slide.indicator || (await getIndicator(tab));
    if (before.endsWith(`/${pageCount}`) && before.startsWith(`${pageCount}/`)) break;
    if (attempt < pageCount + 1) {
      await tab.cua.click({ x: arrows.right.x, y: arrows.right.y });
      await waitForIndicatorChange(tab, before, Math.max(1500, clickDelayMs * 5));
    }
  }
  return slides.filter((slide) => slide.url);
}

function canUseDomSlides(slides, pageCount, observedUrls) {
  if (slides.length < pageCount) return false;
  return !slides.some((slide) => {
    return slide.url.includes("!nd_prv") && !hasObservedUpgrade(slide.url, observedUrls);
  });
}

function hasPreviewSlides(slides) {
  return slides.some((slide) => slide.url.includes("!nd_prv"));
}

async function warmPreviewUpgrades(tab, clickDelayMs) {
  const arrows = await getArrowCenters(tab);
  if (!arrows.right || !arrows.left) return [];
  await tab.cua.click({ x: arrows.right.x, y: arrows.right.y });
  await tab.playwright.waitForTimeout(clickDelayMs);
  const afterRight = await readPostBasics(tab);
  await tab.cua.click({ x: arrows.left.x, y: arrows.left.y });
  await tab.playwright.waitForTimeout(clickDelayMs);
  const afterLeft = await readPostBasics(tab);
  return [
    ...(afterRight.observedImageUrls || []),
    ...(afterLeft.observedImageUrls || []),
  ];
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
  const pageCount = total || 1;
  const domSlides = await collectSlidesFromDom(tab, pageCount);
  const afterDomBasics = await readPostBasics(tab);
  const observedAfterDom = Array.from(
    new Set([...(basics.observedImageUrls || []), ...(afterDomBasics.observedImageUrls || [])]),
  );
  let slides = domSlides;
  let captureMethod = "dom";
  let finalBasics = afterDomBasics;
  if (!canUseDomSlides(domSlides, pageCount, observedAfterDom)) {
    let warmedObserved = observedAfterDom;
    if (domSlides.length >= pageCount && hasPreviewSlides(domSlides)) {
      warmedObserved = Array.from(
        new Set([...observedAfterDom, ...(await warmPreviewUpgrades(tab, clickDelayMs))]),
      );
    }
    if (canUseDomSlides(domSlides, pageCount, warmedObserved)) {
      finalBasics = await readPostBasics(tab);
      captureMethod = "dom-warmed";
    } else {
      const recoveredSlides = recoverSlidesFromObserved(domSlides, pageCount, warmedObserved);
      if (recoveredSlides) {
        slides = recoveredSlides;
        captureMethod = "dom-observed-recovered";
      } else {
        slides = await collectSlides(tab, pageCount, clickDelayMs);
        finalBasics = await readPostBasics(tab);
        captureMethod = "click-fallback";
        warmedObserved = Array.from(
          new Set([...warmedObserved, ...(finalBasics.observedImageUrls || [])]),
        );
        const clickRecoveredSlides = recoverSlidesFromObserved(slides, pageCount, warmedObserved);
        if (clickRecoveredSlides) {
          slides = clickRecoveredSlides;
          captureMethod = "click-fallback-observed-recovered";
        }
      }
    }
    finalBasics.observedImageUrls = Array.from(
      new Set([...(finalBasics.observedImageUrls || []), ...warmedObserved]),
    );
  }
  const capture = {
    ...basics,
    pageCount: pageCount || slides.length,
    slides,
    captureMethod,
    observedImageUrls: Array.from(
      new Set([...(observedAfterDom || []), ...(finalBasics.observedImageUrls || [])]),
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
    captureMethod,
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
    scanLimit: options.scanLimit,
    minScore: options.minScore,
    preferHints: options.preferHints,
    rejectHints: options.rejectHints,
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
