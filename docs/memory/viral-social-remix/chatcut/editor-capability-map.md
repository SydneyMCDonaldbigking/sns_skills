---
tags:
  - chatcut
  - product-map
  - video-editing
aliases:
  - ChatCut 能力地图
updated: 2026-07-28
source: ChatCut product-help UI and features reference
---

# ChatCut 编辑器能力地图

这份笔记只记录已确认的产品能力。主题策略和创意判断放在
[[theme-playbooks]]，不要把两者混成产品承诺。

## 项目入口和预设场景

ChatCut 登录后直接进入编辑器；已有项目时可从项目面板切换或新建项目。
空白 AI 对话中可见的工作流入口包括：

| 场景 | 适合的任务 | 注意 |
| --- | --- | --- |
| `Seedance 2.0` | 根据文字生成视频片段 | Pro only；属于生成任务 |
| `App Promo` | App 或网站宣传片 | 仍要提供真实卖点和界面证据 |
| `URL to Ad Video` | 从商品链接制作 UGC 风短广告 | Pro only；链接不是事实核验的替代品 |
| `Motion Graphics` | 创建可复用动画视觉元素 | 生成前可能出现额度确认 |
| `Talking Head Editing` | 选取好 take、删口头语、收紧节奏并加动效 | 必须以真实讲话内容为准 |
| `Explainer Video` | 主题到完整解释视频，含旁白、画面和 BGM | 事实型内容仍需可靠输入 |

这些场景卡会把起始提示放入 AI 输入框，用户可以先修改再发送。

## 五个主要工作区

### AI Panel

与 Agent 对话并提出剪辑请求。可以用 `@` 引用时间线项目、素材、画面区域、
时间点或 Transcript 文字，让请求指向具体对象。

底部主要控制：

- `Agent`：让 AI 理解上下文并执行完整剪辑任务。
- `Video Gen`：直接进入视频生成流程，适合已经写清楚的生成请求。
- `Agent Settings`：
  - `Thinking Mode`
  - `Motion Graphics Quality`：`Speed`、`Balance`、`Quality`
  - `Generation Auto-Allow`：分别控制 Motion Graphics、Video Generation
    和 Image Generation 的本项目自动允许。
- `+`：上传作为本条消息上下文的图片、视频等文件。
- `Skills`：选择预设或已保存的复用流程，也可以保存当前剪辑过程为 Skill。
- `Selection`：在时间线、My Assets、预览画布、时间尺或 Transcript 中选中
  具体对象，并写成输入框里的 `@` 引用。
- `Send / Stop`：发送请求或停止进行中的任务。

Motion Graphics、Video Generation 和 Image Generation 可能在 AI 区域显示确认卡。
可选择单次允许、本项目全部允许、拒绝或调整。确认卡消失可能代表已回答、
取消或超时，不能自行假设任务仍在运行。

### Preview

中央预览画布显示当前播放头位置的时间线结果。它用于判断构图、遮挡、字幕
安全区、动作连续性和动效观感，不只用于“看有没有画面”。

### My Assets、Library 和 Transcript

- `My Assets`：
  - 管理上传、录制、导入和生成的媒体。
  - 可用 `Upload` 选择 `Files...`、`Folder...` 或 `From phone...`。
  - 生成任务的进度和失败状态会显示在素材卡片上。
  - 可创建 bins/folders 整理素材。
- `Library`：浏览编辑器内建的预设、效果和资产。
- `Templates`：启用时可浏览模板。
- `Transcript`：
  - 适用于 talking head、采访和其他语音主导素材。
  - 删除文字可删除相应视频内容。
  - 拖动文字段可以重排视频顺序。
  - Agent 编辑时可实时看到删除标记并继续细调。
  - 它跟随当前字幕/来源轨；没有指定来源时，使用第一个含视频或音频的轨道。

重要边界：无对白 B-roll 没有可依赖的语义 Transcript。此时应根据画面动作
切分，并用短标签或 Motion Graphics 表达步骤，不能编造转录文字。

### Top Bar

- `Home`：回到项目库。
- 项目名：项目所有者可点击重命名。
- `Share & members`：共享项目和管理成员。
- `Undo / Redo`：撤销或重做。
- `Workspace`：显示/隐藏 AI、My Assets、Library、Transcript 和 Timeline，
  并可 `Reset to default`。
- `Versions`：保存和恢复项目快照。
- `Export`：导出视频、音频、动效、字幕或 XML。
- 用户菜单：语言、外观、反馈、快捷键、Credits history 等。

在进行大范围删词、重排、统一字幕或主题改版前，优先保存一个 `Versions` 快照。

### Timeline

项目可有多条 timelines/sequences，例如长版、竖屏短版和广告精简版。切换
timeline 时素材库共享，但轨道和剪辑项目独立。

- 视频轨在上方：`V1`、`V2`……
- 音频轨在下方：`A1`、`A2`……
- 可拖动项目改位置、拖边裁切、用黄色播放头浏览。
- 每条轨道有可见性、音频和删除控制。
- `I` 标记 In，`O` 标记 Out，`X` 清除区域。
- Export 可以只导出标记的 Zone。

播放区和时间线上方的常用控制：

| 控制 | 用途 |
| --- | --- |
| `Split` / `C` | 在播放头处分割 |
| `Snapping` / `Shift+M` | 拖动时吸附或取消吸附 |
| `Play / Pause` / `Space` | 播放或暂停 |
| Zoom / Zoom to Fit | 放大剪切细节或查看全片结构 |
| Aspect ratio | `16:9`、`9:16`、`1:1`、`4:3`、`3:4` |
| Captions | 自动字幕和内建样式，如 Plain、Netflix、TikTok |
| Fullscreen / `` ` `` | 全屏预览 |

## 能力到剪辑任务的映射

| 想完成的事 | 首选入口 | 低级模型应先确认 |
| --- | --- | --- |
| 精确修改某个镜头 | Selection + `@` 时间线项目 | 项目、时间段和修改范围 |
| 删除口头语/废话 | Transcript | 真实台词、句意和切后连贯 |
| 给无对白料理视频加步骤标签 | Motion Graphics 或 Captions | 标签与画面动作一致 |
| 统一更换可编辑标签样式 | 一个可复用 Motion Graphic，多实例覆盖文字 | 最长文字不会溢出 |
| 做长版和短版 | 多 timeline/sequence | 两版目标、画幅和时长 |
| 只导出一段 | In/Out Zone + Export | Zone 边界是否完整 |
| 尝试大改但保留回退 | Versions | 快照已保存且命名清楚 |
| 检查生成是否完成 | My Assets | 进度、成功或失败状态 |
| 复用稳定流程 | Skills | 流程是否已去除项目专属事实 |

## 导出能力

`Export` 面板有五类：

- `Video`：MP4；分辨率 `1080p`、`720p`、`480p`；可选帧率和全时间线/Zone。
- `Audio`：MP3。
- `Graphics`：把每个 Motion Graphic 分别导出为透明 ProRes 4444 `.mov`
  （Pro only）。
- `Subtitles`：导出字幕。
- `XML`：导出给其他 NLE 使用的 XML；需要时也可包含单独渲染的 Motion
  Graphics。

导出设置只是请求。真正交付前仍要检查下载文件的画面尺寸、总时长、帧率、
音轨、开头和结尾。

## 适合 ChatCut 的编辑思想

ChatCut 特别适合以下可逆、分层的工作方式：

- 用 Transcript 完成语义粗剪，再回时间线检查跳切和呼吸。
- 用多个 timelines 保存长版、短版和平台适配版，而不是覆盖唯一成片。
- 用 Motion Graphic 做统一样式、逐实例换词的字幕/标签系统。
- 用 `@` 精确引用素材或时刻，让 Agent 修改局部而不是重做全片。
- 用 Versions 在高风险重排前保存快照。
- 用 Zone 快速导出局部测试，不必每次渲染整条时间线。
- 用 XML 把项目交给其他 NLE 做更深的 finishing，而不必把流程压平成单个 MP4。
