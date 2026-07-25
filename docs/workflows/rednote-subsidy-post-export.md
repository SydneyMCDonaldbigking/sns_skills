# 小红书补贴帖筛选与素材导出成功流程

适用场景：从公司小红书主页筛选标题、正文或图片里包含关键词的帖子，并按“一帖一文件夹”导出图片本体、文案和 metadata。

## 成功产物结构

```text
output/YYYYMMDD-HHMMSS-rednote-xxx/
  index.md
  manifest.json
  raw/
    screen-scan.json
    screen-ocr-map.json
    detail-extract.json
  screens/
    001.png
  posts/
    post-001-title/
      images/
        01.webp
        02.webp
      content.md
      metadata.json
      raw/detail.json
```

## 推荐流程

1. 用 Chrome 打开公司小红书主页，保留登录态。
2. 对主页做滚动截图和卡片坐标采集。
3. 先在本地对主页截图做 OCR 粗筛，不要一开始逐篇打开。
4. 候选集合取标题命中、主页截图 OCR 命中、详情正文命中、详情原图 OCR 命中的并集。
5. 只打开候选帖子详情页，提取标题、正文、日期、图片 URL 和可见互动信息。
6. 下载每篇帖子原图到 `posts/post-xxx/images/`。
7. 对下载后的原图再次 OCR，确认图片内关键词命中。
8. 每篇生成 `metadata.json` 和 `content.md`。
9. 顶层生成 `index.md` 和 `manifest.json`。

## 已验证脚本

- `viral-social-remix/scripts/map_rednote_profile_ocr.py`：把主页截图 OCR 命中映射回帖子卡片。
- `viral-social-remix/scripts/export_rednote_subsidy_posts.py`：根据详情提取结果导出帖子文件夹、下载图片、跑原图 OCR、生成索引。

## 关键经验

- 先 OCR 主页截图，再打开详情页，最省 token。
- 小红书正文优先从详情页 meta description 取，比大段 DOM 文本干净。
- 图片下载要带 `User-Agent` 和 `Referer: https://www.rednote.com/`。
- 浏览器滚动如果 CUA 超时，可以用页面脚本 `window.scrollTo()` 控制。
- “置顶”等卡片标题可能不是原帖标题，不能只靠标题判断；正文和图片 OCR 命中也要纳入。

## 避免踩坑

- 不要把网页截图当素材本体；截图只做证据。
- 不要一个帖子一张图就结束；轮播帖要点进详情提取全部图片。
- 不要把 `output/` 提交进 git；素材本地保留即可。
- PowerShell/conda 遇到中文输出可能 GBK 崩溃，优先直接调用环境里的 `python.exe -X utf8`。
