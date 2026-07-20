# Viral Social Remix Skill

把小红书、Instagram/Facebook 图片帖、浏览器中已登录可见的社媒内容或本地视频素材拆解为可复用的内容结构，再结合品牌与产品素材，准备平台可发布的图片轮播、九帧视频故事板和配套文案。

仓库包含 Codex Skill、确定性媒体处理脚本、素材索引工具、浏览器 source capture 工具、OpenRouter 本地生成 runner、输出校验器以及测试。核心使用说明见 [`viral-social-remix/SKILL.md`](viral-social-remix/SKILL.md)。

## 支持范围

- 小红书图片轮播：保留源帖页数，默认输出 `1152x1536` 中文竖图。
- Instagram/Facebook 图片轮播：保留源帖页数，输出 `1152x1152` 自然英文方图。
- 视频 storyboard：筛选九个叙事节点，输出 `1920x1080` 关键帧与 16:9 九宫格总览。
- 浏览器 source capture：把已登录浏览器中可见的社媒内容打包成本地 source package。
- 本地素材记忆：索引已整理的社媒帖子和品牌官网素材，减少重复采集。
- 断点恢复：通过 `manifest.json` 跳过已经校验或已生成到正确尺寸的产物。

## 环境要求

- Conda（推荐）或 Python 3.11 以上版本。
- FFmpeg 和 FFprobe；仅视频抽帧需要。
- OpenRouter API key；仅调用默认图片生成提供商时需要。

### 推荐安装方式

在仓库根目录运行：

```powershell
conda env create -f environment.yml
conda activate sns_skill_dev
```

如果环境已经存在：

```powershell
conda env update -f environment.yml --prune
conda activate sns_skill_dev
```

如果 Conda 插件或 TOS cache 在 Windows 上卡住，可以改用本地 prefix 环境：

```powershell
conda --no-plugins create --solver classic --prefix .\.venv -y python=3.11 pillow pyyaml pytest
conda activate .\.venv
```

需要本地 OCR 时再安装可选依赖：

```powershell
python -m pip install -e ".[ocr,test]"
```

不使用 Conda 时，可以在已经安装 FFmpeg 的 Python 环境中运行：

```powershell
python -m pip install -e ".[test]"
```

## 配置图片生成

脚本会读取仓库根目录的 `.env.local`。该文件及其他本地环境文件均被 Git 忽略。可用变量如下：

```dotenv
OPENROUTER_API_KEY=<your-key>
VSR_IMAGE_PROVIDER=openrouter
VSR_IMAGE_MODEL=openai/gpt-5.4-image-2
VSR_IMAGE_QUALITY=medium
VSR_IMAGE_ENDPOINT=
```

查看已解析的脱敏配置：

```powershell
python viral-social-remix/scripts/image_provider.py
python viral-social-remix/scripts/image_provider.py --require-key
```

命令只输出 `api_key_set`，不会打印 API key。

轮播图片生成默认通过用户本地终端运行：

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output/<run-dir> --api-only --concurrency 2
```

runner 会读取 `analysis/manifest.json`、`analysis/page-prompts/page-XX.md` 和 manifest 中登记的 reference images，写回 `generated/`、`raw/`、`overview/contact-sheet.png`、`qa/validation.json` 和 `qa/openrouter-cost.json`。

## 快速验证

```powershell
python -m pytest
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" viral-social-remix
```

第二条命令依赖本机 Codex 内置的 `skill-creator`。没有该目录时，运行测试即可完成仓库内置的结构校验。

Live OpenRouter contract test 默认跳过。确认 `.env.local` 中已设置 `OPENROUTER_API_KEY` 后，可以显式运行一次：

```powershell
$env:VSR_RUN_LIVE_TESTS = "1"
python -m pytest tests/test_openrouter_image.py -k live -s
```

视频流程还应检查外部工具：

```powershell
ffmpeg -version
ffprobe -version
```

## 常用工作流

### 1. 扫描本地媒体

```powershell
python viral-social-remix/scripts/scan_media.py <media-folder>
python viral-social-remix/scripts/scan_media.py <media-folder> --output output/scan-report.json
```

每个直接子文件夹会被视为一个内容组，根目录中的单个媒体文件会被视为独立任务。`output/`、隐藏目录和不支持的格式会被跳过。

### 2. 使用最小 pipeline

```powershell
python viral-social-remix/scripts/run_pipeline.py scan incoming
python viral-social-remix/scripts/run_pipeline.py prepare incoming/carousel-a --platform xiaohongshu
python viral-social-remix/scripts/run_pipeline.py pending output/<run-dir>/analysis/manifest.json
python viral-social-remix/scripts/run_pipeline.py generate output/<run-dir> --asset-id 01 --dry-run
python viral-social-remix/scripts/run_pipeline.py validate output/<run-dir> --platform xiaohongshu
```

`prepare` 创建标准 run 目录、复制源素材、写入 analysis 占位文件并初始化 manifest；它不会自动分析内容，也不会调用图片生成 API。`pending` 会列出未 `validated` 的 asset ids。`generate` 会按 manifest 平台推断默认尺寸，默认读取 `analysis/prompts.md`、写入 `generated/`，并复用 OpenRouter 的 dry-run、retry、manifest 状态写回和 validated-skip 逻辑。

`prepare` 也接受直接指向图片或视频文件的公开 URL：

```powershell
python viral-social-remix/scripts/run_pipeline.py prepare https://example.com/media/cover.jpg --platform instagram-facebook
```

URL 输入只支持直接媒体文件。HTML 社媒页面、登录页、反爬页面或无法识别的内容不会被解析；请先下载媒体或提供本地文件夹。

### 3. 打包浏览器 source capture

对于已登录浏览器中可见的小红书、Instagram 或 Facebook 内容，先导出浏览器观察到的结构化 JSON，再运行：

```powershell
python viral-social-remix/scripts/capture_source_package.py capture.json --output-dir samples/<source-slug>
```

source package 应至少保留 `metadata.json`、可见 caption、媒体 URL 证据、按顺序导出的 `images/01.*` 等素材，以及必要时的截图 fallback。

### 4. 检索本地素材索引

```powershell
python viral-social-remix/scripts/query_material_index.py 补贴 --platform rednote
python viral-social-remix/scripts/query_material_index.py pantry --platform instagram_facebook --type post
```

索引默认为 `data/material-index.jsonl`，属于本地数据，不提交到 Git。完整流程见 [`docs/workflows/local-material-index.md`](docs/workflows/local-material-index.md)。

创建一次标准复刻任务：

```powershell
python viral-social-remix/scripts/prepare_remix_run.py `
  --task-name rednote-subsidy-rice `
  --source-platform rednote `
  --source-query 补贴 `
  --product-query rice
```

生成前检查任务骨架：

```powershell
python viral-social-remix/scripts/validate_prepared_run.py output/<run>
```

### 5. 视频候选帧

先导出用于审阅的候选帧：

```powershell
python viral-social-remix/scripts/extract_keyframes.py candidates source.mp4 output/<run>/references/keyframes --count 18
```

审阅后按九个叙事节点选择时间戳并导出最终关键帧：

```powershell
python viral-social-remix/scripts/extract_keyframes.py selected source.mp4 output/<run>/references/keyframes `
  --timestamps 0.8 2.4 4.1 6.0 8.2 10.5 12.7 15.0 17.4
```

候选帧可以等间隔获取，但最终九帧必须按叙事功能筛选。

### 6. 总览与输出校验

先为已经逐图审阅和校验的轮播生成总览：

```powershell
$images = Get-ChildItem output/<run>/generated/*.png | ForEach-Object FullName
python viral-social-remix/scripts/make_contact_sheet.py carousel @images --output output/<run>/overview/contact-sheet.png
```

视频使用 `storyboard` 子命令并传入恰好九张图片；默认标签为 Hook、Setup、Pain、Product、Mechanism、Benefit、Proof、Result 和 CTA。

最后校验完整交付包并写入 `qa/validation.json`：

```powershell
python viral-social-remix/scripts/validate_output.py delivery output/<run> --platform xiaohongshu
```

## 品牌资料

默认品牌资料在 `viral-social-remix/brand-profile.md`。使用前先确认：

- 品牌名称
- 产品名称
- 核心卖点
- Logo 或产品素材路径
- 禁止内容

当前任务中用户明确给出的品牌或产品信息会覆盖默认资料。

## 目录结构

```text
viral-social-remix/   Codex Skill、脚本、参考文档和品牌资产
tests/                单元测试与端到端夹具测试
docs/workflows/       素材采集、索引和平台导出流程
data/                 本地素材索引及缓存（多数不提交）
output/               每次任务的时间戳产物（不提交）
```

每次任务都会写入新的 `output/YYYYMMDD-HHmmss-<task>/`，不会覆盖已有产物。

## 常用脚本

- `scan_media.py`：扫描本地素材并分组。
- `capture_source_package.py`：把浏览器观察到的来源 JSON 打包为本地 source package。
- `run_pipeline.py`：提供 scan、prepare、pending、generate 和 validate 的最小 pipeline 入口。
- `prepare_remix_run.py`：按素材索引和品牌资产创建标准复刻任务骨架。
- `manifest.py`：维护每张资产的生成状态，支持中断续跑。
- `extract_keyframes.py`：用 FFmpeg / FFprobe 抽视频候选帧和 9 个关键帧。
- `make_contact_sheet.py`：生成轮播总览图或视频九宫格。
- `run_openrouter_carousel.py`：从本地终端上传 page prompts 和 reference images，按页生成轮播图片。
- `validate_output.py`：检查输出文件、尺寸和 manifest 完成状态。
- `ocr_rednote_images.py`：OCR 图片并按关键词过滤，需额外 OCR 依赖。

## 开发约定

- 不提交 `.env`、`.env.*`、API key、本地素材索引、下载媒体或生成产物。
- 修改 Skill 或脚本后运行完整测试。
- 平台细节放进 `references/`，保持 `SKILL.md` 聚焦于决策和执行流程。
- 网页截图只作为证据，不能代替原始图片或视频素材。

## 当前边界

- 公开 URL 抓取仍依赖 Codex 当前可访问能力；遇到登录、反爬或不可读页面时，应让用户上传媒体、打开可控浏览器标签页或提供本地 source package。
- 轮播 API 图片生成应由用户本地 runner 发起；Codex 环境如果无法上传 reference assets，不应绕过限制。
- 图片中文字和产品包装仍需要视觉复核；自动校验只能覆盖尺寸、文件结构和 manifest 状态。
