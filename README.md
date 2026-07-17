# Viral Social Remix Skill

这是一个 Codex skill，用来把爆款社媒素材拆解并重制成品牌化内容。当前重点支持：

- 小红书图片轮播：中文，默认 `1152x1536`，页数跟随源素材。
- Instagram/Facebook 图片轮播：自然英文，`1152x1152`，页数跟随源素材。
- 视频 storyboard：固定 9 个叙事关键帧，`1920x1080`，并生成 16:9 九宫格总览图。

核心 skill 在 `viral-social-remix/SKILL.md`，平台规格、输出结构和提示词合同在 `viral-social-remix/references/`。

## 环境

推荐使用仓库内 conda 环境：

```powershell
conda create --prefix .\.venv -y python=3.11 pillow pyyaml pytest
conda activate C:\Users\uryuu\Desktop\sns_skill\.venv
```

如果 conda 插件或 TOS cache 在 Windows 上卡住，可以改用：

```powershell
conda --no-plugins create --solver classic --prefix .\.venv -y python=3.11 pillow pyyaml pytest
conda activate C:\Users\uryuu\Desktop\sns_skill\.venv
```

运行测试：

```powershell
python -m pytest
```

Live OpenRouter contract test 默认跳过。确认 `.env.local` 中已设置
`OPENROUTER_API_KEY` 后，可以显式运行一次：

```powershell
$env:VSR_RUN_LIVE_TESTS = "1"
python -m pytest tests/test_openrouter_image.py -k live -s
```

## 使用方式

把待分析素材放在一个本地目录中。推荐结构：

```text
incoming/
├── carousel-a/
│   ├── 01.jpg
│   └── 02.jpg
├── carousel-b/
│   ├── 01.png
│   └── 02.png
└── single-video.mp4
```

扫描本地素材：

```powershell
python viral-social-remix/scripts/scan_media.py incoming
```

每个直接子文件夹会被视为一个内容组，根目录中的单个媒体文件会被视为独立任务。`output/`、隐藏目录和不支持的格式会被跳过。

也可以使用最小 pipeline 入口：

```powershell
python viral-social-remix/scripts/run_pipeline.py scan incoming
python viral-social-remix/scripts/run_pipeline.py prepare incoming/carousel-a --platform xiaohongshu
python viral-social-remix/scripts/run_pipeline.py pending output/<run-dir>/analysis/manifest.json
python viral-social-remix/scripts/run_pipeline.py generate output/<run-dir> --asset-id 01 --dry-run
python viral-social-remix/scripts/run_pipeline.py validate output/<run-dir> --platform xiaohongshu
```

`prepare` 只创建标准 run 目录、复制源素材、写入 analysis 占位文件并初始化 manifest；它不会自动分析内容，也不会调用图片生成 API。
`pending` 会列出未 `validated` 的 asset ids。`generate` 会按 manifest 平台推断默认尺寸，默认读取 `analysis/prompts.md`、写入 `generated/`，并复用 OpenRouter 的 dry-run、retry、manifest 状态写回和 validated-skip 逻辑。

`prepare` 也接受直接指向图片或视频文件的公开 URL：

```powershell
python viral-social-remix/scripts/run_pipeline.py prepare https://example.com/media/cover.jpg --platform instagram-facebook
```

URL 输入只支持直接媒体文件。HTML 社媒页面、登录页、反爬页面或无法识别的内容不会被解析；请先下载媒体或提供本地文件夹。

## 品牌资料

默认品牌资料在 `viral-social-remix/brand-profile.md`。使用前先确认：

- 品牌名称
- 产品名称
- 核心卖点
- Logo 或产品素材路径
- 禁止内容

当前任务中用户明确给出的品牌或产品信息会覆盖默认资料。

## 输出

每次运行应该创建新的输出目录，不覆盖旧结果：

```text
output/YYYYMMDD-HHmmss-<task>/
├── source/
├── analysis/
│   ├── breakdown.md
│   ├── copy.md
│   ├── caption-zh.txt
│   ├── caption-en.txt
│   ├── prompts.md
│   └── manifest.json
├── references/keyframes/
├── generated/
├── overview/contact-sheet.png
└── qa/validation.json
```

小红书任务必须有 `caption-zh.txt`，Instagram/Facebook 任务必须有 `caption-en.txt`。视频任务使用目标发布平台对应的 caption 语言。

## 图片生成

图片生成默认通过 OpenRouter：

- 环境变量：`OPENROUTER_API_KEY`
- 默认模型：`openai/gpt-5.4-image-2`
- 默认质量：`medium`

本地可以放一个被 git 忽略的 `.env.local`：

```text
OPENROUTER_API_KEY=...
```

不要提交 `.env`、`.env.*`、API key、vendor 原始响应或包含 Authorization header 的请求日志。

检查 provider 配置：

```powershell
python viral-social-remix/scripts/image_provider.py
```

生成前预检请求 payload，不调用 API：

```powershell
python viral-social-remix/scripts/openrouter_image.py --prompt-file output/<run-dir>/analysis/prompts.md --out-dir output/<run-dir>/generated --size 1152x1536 --dry-run
```

真实生成时可以把失败写回 manifest。相同 OpenRouter HTTP 错误连续出现两次会停止重试：

```powershell
python viral-social-remix/scripts/openrouter_image.py --prompt-file output/<run-dir>/analysis/prompts.md --out-dir output/<run-dir>/generated --size 1152x1536 --manifest output/<run-dir>/analysis/manifest.json --asset-id 01 --max-attempts 2
```

真实请求发出前，该 asset 会被标记为 `prompted`，并记录 prompt 路径和脱敏 request payload。
保存到图片后，该 asset 会被标记为 `generated`，并记录输出路径。若 OpenRouter 响应成功但没有返回任何图片，该 asset 会被标记为 `failed`。
如果 manifest 中该 asset 已经是 `validated`，默认会跳过生成；需要重生时加 `--force`。

如果没有 key，skill 仍然可以继续做素材扫描、拆解、文案、prompts、manifest 和 contact sheet；只应暂停真实图片生成。

## 常用脚本

- `scan_media.py`：扫描本地素材并分组。
- `create_run_dir.py`：创建不会覆盖旧结果的时间戳目录。
- `manifest.py`：维护每张资产的生成状态，支持中断续跑。
- `extract_keyframes.py`：用 `ffmpeg` / `ffprobe` 抽视频候选帧和 9 个关键帧。
- `make_contact_sheet.py`：生成轮播总览图或视频九宫格。
- `reframe_image.py`：把图片裁切或补边到目标社媒尺寸。
- `validate_output.py`：检查输出文件、尺寸和 manifest 完成状态。
- `clean_rednote_export.py`：清洗 Rednote / 小红书导出内容。
- `ocr_rednote_images.py`：OCR 图片并按关键词过滤，需额外 OCR 依赖。

## 当前边界

- 仓库目前主要提供 skill 说明、确定性脚本和测试，还没有完整的一条命令端到端 pipeline。
- 公开 URL 抓取仍依赖 Codex 当前可访问能力；遇到登录、反爬或不可读页面时，应让用户上传媒体或提供本地文件夹。
- 图片中文字和产品包装仍需要视觉复核；自动校验只能覆盖尺寸、文件结构和 manifest 状态。
