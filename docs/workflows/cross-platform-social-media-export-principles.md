# 跨平台社媒素材导出总原则

适用平台：小红书、Instagram、Facebook，以及后续 TikTok / Reels / 视频关键帧流程。

## 核心标准

以后所有“爆款筛选 / 复刻参考 / 素材提取”任务，都按同一个交付标准：

```text
一篇帖子 = 一个文件夹
图片/视频本体 = 单独放 media 或 images
文案 = 单独放 caption.txt
结构化信息 = metadata.json
人工可读摘要 = content.md
原始提取数据 = raw/
```

不要只交付网页截图、页面分析或 prompt。截图只能作为证据，不能替代素材本体。

## 标准产物结构

```text
output/YYYYMMDD-HHMMSS-task-name/
  index.md 或 posts_index.md
  manifest.json 或 posts_manifest.json
  source/
    page-screenshots/
    candidate-details.json
  posts/
    post-001-title-or-id/
      images/
        01.jpg
        02.jpg
      caption.txt
      content.md
      metadata.json
      raw/
        detail.json
```

视频任务可以改成：

```text
post-001-title-or-id/
  video/
    source.mp4
  keyframes/
    01.jpg
    02.jpg
  contact-sheet.jpg
  caption.txt
  content.md
  metadata.json
```

## 必须分离的东西

- 图片本体：原帖图片、视频关键帧、下载下来的媒体文件。
- 网页截图：只做证据，放 `source/`，不要混进 `posts/images/`。
- 原文案：放 `caption.txt`。
- 复刻文案：放 `analysis/` 或 `copy/`，不要覆盖原文案。
- 分析判断：放 `content.md`、`selection.md`、`remix-brief.md`。

## 平台差异

### 小红书

- 先用主页截图 OCR 粗筛关键词。
- 再打开候选详情页。
- 下载每篇所有原图。
- 对下载后的原图再次 OCR 复核。
- 正文优先取详情页 meta description。

参考：[[小红书补贴帖筛选与素材导出成功流程]]

### Instagram / Facebook

- 先筛爆款机制：保存价值、互动信号、可复刻性、Umall 贴合度。
- 页面截图只做证据。
- 必须下载 IG 媒体图片本体。
- 原帖 caption 单独保存为 `caption.txt`。
- 复刻 brief 和英文 caption 放 `analysis/`。

参考：[[Instagram Facebook 爆款候选筛选与素材导出成功流程]]

## 经验教训

- 不要把“选题 brief”误当成“素材整理完成”。
- 不要把网页截图误当成图片素材。
- 不要混合原帖文案和复刻文案。
- 不要因为 IG 是英文平台，就忘了小红书已经跑通的文件夹标准。
- 任何平台都先问：我有没有拿到媒体本体？有没有把文案分开放？

## 最短检查清单

交付前必须回答：

1. 每篇帖子是不是一个独立文件夹？
2. 图片/视频本体是不是在 `images/` 或 `video/`？
3. 文案是不是单独在 `caption.txt`？
4. 有没有 `metadata.json`？
5. 有没有总索引？
6. 网页截图有没有和素材本体分开？
7. `output/` 是否仍被 git 忽略？
