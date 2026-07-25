# Instagram / Facebook 爆款候选筛选与素材导出成功流程

适用场景：为 Umall 找英文 IG/FB 爆款参考，并按“小红书同款结构”导出图片本体、caption、分析和 metadata。

## 成功产物结构

```text
output/YYYYMMDD-HHMMSS-ig-viral-selection-refined/
  posts_index.md
  posts_manifest.json
  analysis/
    selection.md
    remix-brief.md
    caption-en.txt
    manifest.json
  source/
    ig-candidate-details.json
    candidate-page-screenshot.png
  posts/
    post-001-source-id/
      images/
        01.jpg
        02.jpg
      caption.txt
      content.md
      metadata.json
      raw/detail.json
```

## 推荐流程

1. 先确定筛选标准：爆款信号、可复刻性、Umall 贴合度、保存价值。
2. 用 Chrome/登录态少量搜索候选，不要大范围爬。
3. 每轮只进少数强候选详情页，提取 IG meta description、账号、caption、互动数据、图片 URL、视频信息和页面截图证据。
4. 先做候选评分，选出主选、执行模板、生活化备选和视频备选。
5. 必须导出图片本体：每个候选一个 `posts/post-xxx/`，`images/` 放 IG 媒体图片本体，`caption.txt` 单独保存原帖文案。
6. 最后生成 `posts_index.md`、`posts_manifest.json`、`analysis/selection.md`、`analysis/remix-brief.md` 和 `analysis/caption-en.txt`。

## 已验证判断模板

主选机制可以来自 `_sam_low_` 类型：

- 教用户“如何逛亚洲超市”。
- 知识型、保存型、系列感强。
- 可转成 Umall 的“线上亚洲超市不迷路”教育内容。

执行模板可以来自 `littlebaoboy` 类型：

- 手持商品 + 货架背景。
- 白色贴纸短文案。
- 一页一个品类 / 一句用法。
- 很适合 1152×1152 方图轮播。

## IG/FB 推荐复刻方向

标题：

```text
How to shop Asian groceries online without getting overwhelmed
```

轮播结构：

1. Cover：How to shop Asian groceries online without getting overwhelmed
2. Sauces first：soy sauce, oyster sauce, cooking wine
3. Heat + flavour：chilli crisp, gochugaru, curry paste
4. Weeknight backup：dumplings, noodles, soup bases
5. Fresh + freezer：veg, tofu, hotpot, seafood/meat
6. Snacks + drinks：the fun part of the restock
7. Heavy staples：rice, drinks, oils — the reason delivery wins
8. CTA：Build the box on Umall and save the list

## 关键经验

- IG 不能只留页面截图和分析；必须像小红书一样导出图片本体。
- 网页截图只做证据，不是素材。
- caption 必须和图片分开放。
- 作者原图里自带的贴纸文字属于图片本体，可以保留；网页 caption 不要混进图片文件。
- IG 图片下载要带 `User-Agent` 和 `Referer: https://www.instagram.com/`。
- `output/` 不进 git；只把流程、脚本、模板提交。

## 避免踩坑

- 不要把“选题 brief”当作最终素材整理。
- 不要只看互动；还要看能不能复刻成 Umall 的方图结构。
- 不要优先低互动商家帖；它们可以借 caption 结构，但不适合作“爆款参考”。
- 视频候选要标为视频备选，后续单独走关键帧流程。
