# Viral Social Remix Skill

把小红书、Instagram/Facebook 图片帖或本地视频素材拆解为可复用的内容结构，再结合品牌与产品素材，准备平台可发布的图片轮播、九帧视频故事板和配套文案。

仓库包含 Codex Skill、确定性媒体处理脚本、素材索引工具、输出校验器以及测试。核心使用说明见 [`viral-social-remix/SKILL.md`](viral-social-remix/SKILL.md)。

## 支持范围

- 小红书图片帖：保留源帖页数，默认输出 `1152x1536` 中文竖图。
- Instagram/Facebook 图片帖：保留源帖页数，输出 `1152x1152` 英文方图。
- 视频：筛选九个叙事节点，输出 `1920x1080` 关键帧与九宫格总览。
- 本地素材记忆：索引已整理的社媒帖子和品牌官网素材，减少重复采集。
- 断点恢复：通过 `manifest.json` 跳过已经校验的产物。

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

## 快速验证

```powershell
python -m pytest
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" viral-social-remix
```

第二条命令依赖本机 Codex 内置的 `skill-creator`。没有该目录时，运行测试即可完成仓库内置的结构校验。

视频流程还应检查外部工具：

```powershell
ffmpeg -version
ffprobe -version
```

## 常用工作流

### 1. 扫描本地媒体

```powershell
python viral-social-remix/scripts/scan_media.py <media-folder>
```

### 2. 检索本地素材索引

```powershell
python viral-social-remix/scripts/query_material_index.py 补贴 --platform rednote
python viral-social-remix/scripts/query_material_index.py pantry --platform instagram_facebook --type post
```

索引默认为 `data/material-index.jsonl`，属于本地数据，不提交到 Git。完整流程见 [`docs/workflows/local-material-index.md`](docs/workflows/local-material-index.md)。

### 3. 创建一次标准复刻任务

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

### 4. 视频候选帧

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

### 5. 总览与输出校验

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

## 目录结构

```text
viral-social-remix/   Codex Skill、脚本、参考文档和品牌资产
tests/                单元测试与端到端夹具测试
docs/workflows/       素材采集、索引和平台导出流程
data/                 本地素材索引及缓存（多数不提交）
output/               每次任务的时间戳产物（不提交）
```

每次任务都会写入新的 `output/YYYYMMDD-HHmmss-<task>/`，不会覆盖已有产物。

## 开发约定

- 不提交 `.env`、`.env.*`、API key、本地素材索引或生成产物。
- 修改 Skill 或脚本后运行完整测试。
- 平台细节放进 `references/`，保持 `SKILL.md` 聚焦于决策和执行流程。
- 网页截图只作为证据，不能代替原始图片或视频素材。
