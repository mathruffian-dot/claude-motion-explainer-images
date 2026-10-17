# claude-motion-explainer-images

**用一句話，讓 coding agent 做出一支「有圖有證據」的原理解說動畫。** 這是 [claude-motion-explainer](https://github.com/mathruffian-dot/claude-motion-explainer) 的圖片加強版。動畫負責講原理，再加上兩種圖片：

1. **網路上的授權照片**：從 Wikimedia Commons（含 NASA 等公有領域照片）找圖，只收公有領域、CC0、CC BY、CC BY-SA，來源自動記錄，畫面上會標示作者和授權。用來當**證據卡**，告訴觀眾「這真的有人做過」。
2. **Codex CLI 生成的示意圖**：用本機 Codex 的 imagegen 技能（內建 image_gen，不需要 API key）生成沒有品牌、沒有文字的示意圖，配色自動對齊主題。用在開場和收尾的**氣氛背景**，畫面上標「AI 生成示意圖」。

照片會轉成主題的雙色（背景色＋主色），融進動畫的配色；強調色仍然只留給答案和關鍵數字。

> 與 Anthropic 官方的 Claude Motion 無關。這是社群做的開源工作流。

## 範例

〈Tesla Roadster 的三個神奇配備〉，105 秒、9 格，黑底、白字、橘色重點，全片使用源石黑體粗體：

- **開場**：生成圖「車子倒掛在環形軌道上」當背景。
- **倒掛原理**：McMurtry Spéirling 風扇吸地車的照片（CC BY-SA 4.0）當證據卡。
- **冷氣推進器**：NASA 1984 年載人機動裝置的照片（公有領域）當證據卡。
- **收尾**：生成圖「懸浮的跑車」當背景。

## 包含的 skills

| Skill | 做什麼 |
|---|---|
| [`motion-explainer-images`](skills/motion-explainer-images/SKILL.md) | **主流程**：研究 → 需求訪談（三色＋字型）→ 分鏡與子句化旁白 → TTS → 每格平行製作 → 字幕 → 套色 → **圖片層** → 審查 → 輸出 |
| [`motion-design`](skills/motion-design/SKILL.md) | 品味規則：緩動、節奏、閱讀停留、繁體中文排版、三色配色 |
| [`review-loop`](skills/review-loop/SKILL.md) | 自我審查：在每個旁白子句截一格拼成 contact sheet，逐張檢查 |

圖片層的完整規則（授權、擺放、踩過的坑）見 [`references/images.md`](skills/motion-explainer-images/references/images.md)；製作動畫本身的 26 個坑見 [`lessons.md`](skills/motion-explainer-images/references/lessons.md)。

唸錯字也有工具：整支片做完才發現某個字唸錯（例如英文品牌名、破音字），用 `fix_voice.py` 產生試聽檔，讓你用耳朵從幾個候選裡挑一個，再把那一句**整句等比伸縮回原本的長度**換進去。每一格的長度都不變，動畫不用重做。

## 需要的環境

- Node.js 22+、ffmpeg、Python 3 + Pillow + fonttools（`pip install pillow fonttools`）
- HyperFrames：`npm install -g hyperframes`，再跑 `hyperframes skills update` 和 `hyperframes skills update faceless-explainer`
- **生成圖（選用）**：已登入的 [Codex CLI](https://github.com/openai/codex)。沒有的話，可以用任何生圖工具把 PNG 放進 `assets/images/gen/`。
- 旁白（擇一，詳見 [`tts-setup.md`](skills/motion-explainer-images/references/tts-setup.md)）：**edge-tts**（預設，`pip install edge-tts`，不需要 GPU）或 **Breeze TTS 2**（本機 NVIDIA GPU，僅限非商業用途）。
- 先跑 `python skills/motion-explainer-images/scripts/hw_check.py`，它會依你的硬體給建議（[`hardware.md`](skills/motion-explainer-images/references/hardware.md)）。

## 安裝

```bash
git clone https://github.com/mathruffian-dot/claude-motion-explainer-images.git
cp -r claude-motion-explainer-images/skills/* ~/.claude/skills/        # Claude Code
# Codex / 其他 agent：複製到 ~/.agents/skills/
```

可以和基本版 `motion-explainer` 一起安裝。兩者共用的 `motion-design`、`review-loop` 內容完全一樣。

字型不放在 repo 裡（都是開源 OFL）：`bash skills/motion-explainer-images/scripts/fetch_fonts.sh <專案資料夾>` 會下載**源石黑體粗體**（預設全片字型）和製作時用的字型。

## 怎麼用

```text
上網查資料，做一支 90 秒、解說「為什麼飛機飛得起來」的動畫，給國中生上課用。加上真實照片當佐證，開場和結尾用生成圖。
```

Agent 會先問你播放平台、長度、旁白聲音、三個顏色和字型（預設黑底、白字、橘色重點，源石黑體粗體），做好動畫後找照片、生成示意圖、放進畫面，再交給你 MP4 和一張總覽圖。

## 三色主題、字型、圖片

```json
// theme.json
{ "bg": "#121212", "fg": "#F2F0EA", "accent": "#FF7A1A",
  "font": { "family": "GenSekiGothic", "file": "GenSekiGothic2TW-B.otf", "weight": 700 } }
```

`images.json` 描述每張圖怎麼裁切、怎麼套色、放在哪一格、什麼時候出現（範例：[`images.example.json`](skills/motion-explainer-images/templates/images.example.json)）。換主題、換字型、換圖片，都只要改設定、重跑腳本，不用重做動畫。

## English

The image-enhanced edition of [claude-motion-explainer](https://github.com/mathruffian-dot/claude-motion-explainer): agent skills that turn one sentence into a narrated, captioned explainer animation on HyperFrames, plus an image layer — freely licensed photos from Wikimedia Commons (PD / CC0 / CC BY / CC BY-SA only, credits recorded and shown on screen) as evidence cards, and unbranded illustrations generated through the local Codex CLI's imagegen skill as atmosphere backgrounds. Photos are duotoned into the film's three-color theme; one font (GenSeki Gothic Bold by default) for all text. See `skills/motion-explainer-images/SKILL.md`.

## 授權

程式碼與文件採 [MIT](LICENSE)。`motion-design` 和 `review-loop` 改編自 [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion)（MIT），其他第三方元件見 [NOTICE.md](NOTICE.md)。透過本工具下載的照片，各自遵守原作者的授權。
