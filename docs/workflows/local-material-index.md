# 本地素材索引流程

目标：让 skill 记住已经整理过的小红书、Instagram/Facebook、Umall 官网素材，减少重复搜索、重复问用户、重复消耗 token。

## 索引文件

- 默认路径：`data/material-index.jsonl`
- 格式：一行一条 JSON，append-only，方便增量追加。
- 每条记录带稳定 `record_id`，重复运行同一批素材会自动跳过已存在记录。
- Git 策略：索引文件本身不提交；脚本、测试、流程文档提交。

## 什么时候写入索引

每次完成一批可复用素材整理后写入：

- 小红书：一个帖子一个文件夹，记录标题、来源、原因、图片路径、`content.md`。
- Instagram/Facebook：一个帖子一个文件夹，记录 caption、图片路径、指标和来源。
- 品牌官网：记录官方商品图、banner、分类图、品牌图等素材。

## 命令

```bash
python viral-social-remix/scripts/collect_source_assets.py --platform rednote --run-dir output/<rednote-run>
python viral-social-remix/scripts/collect_source_assets.py --platform instagram --run-dir output/<ig-run>
python viral-social-remix/scripts/collect_source_assets.py --platform brand-site --run-dir output/<brand-site-run>
```

预览但不写入：

```bash
python viral-social-remix/scripts/collect_source_assets.py --platform brand-site --run-dir output/<run> --dry-run
```

## 检索素材

按关键词、平台、类型、素材 kind 检索：

```bash
python viral-social-remix/scripts/query_material_index.py 补贴 --platform rednote
python viral-social-remix/scripts/query_material_index.py pantry --platform instagram_facebook --type post
python viral-social-remix/scripts/query_material_index.py 大米 --platform brand_site --type asset --kind product_or_promo
python viral-social-remix/scripts/query_material_index.py wagyu --platform brand_site --quality medium --use-case promotion-reference
```

默认输出 Markdown，适合直接复制进分析文档。需要程序读取时用 JSON：

```bash
python viral-social-remix/scripts/query_material_index.py 大米 --format json
```

## 精修官网素材

官网抓取后先生成精修 catalog，再登记进本地索引：

```bash
python viral-social-remix/scripts/enrich_brand_assets.py --run-dir output/<brand-site-run>
python viral-social-remix/scripts/collect_source_assets.py --platform brand-site --run-dir output/<brand-site-run>
```

精修 catalog 会从 alt、CDN 文件名和尺寸中推断：

- `title`：更可读的商品/场景名称。
- `tags`：如 `rice`、`meat`、`discount`、`category`。
- `use_case`：如 `product-pack-reference`、`product-scene-reference`、`campaign-background`。
- `quality`：`high`、`medium`、`needs-review`。

## 生成复刻上下文包

从本地索引里一次性取“源爆款候选 + 官网商品参考”，用于后续拆解和生成：

```bash
python viral-social-remix/scripts/build_remix_context.py \
  --source-platform rednote \
  --source-query 补贴 \
  --product-query rice \
  --output output/<run>/analysis/remix-context.md
```

IG/FB 示例：

```bash
python viral-social-remix/scripts/build_remix_context.py \
  --source-platform instagram_facebook \
  --source-query pantry \
  --product-query wagyu
```

## 当前初始化结果

2026-07-14 已把以下三批本地素材登记进索引：

- 小红书补贴帖：7 篇帖子。
- Instagram/Facebook 爆款候选：6 篇帖子。
- Umall 官网素材：105 个官方素材。

合计：118 条索引记录。

## 设计原则

- 只索引路径和元数据，不复制素材本体。
- 产物仍然保持“一篇帖子一个文件夹”，图片和文案分开。
- 官方商品图优先用于商品参考，降低 AI 乱写包装中文字的风险。
- 后续生成前先查索引；索引没有或不确定时，再浏览/截图/OCR/询问用户。
