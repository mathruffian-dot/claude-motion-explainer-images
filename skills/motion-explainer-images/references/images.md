# 圖片層：什麼時候用、去哪裡找、怎麼放

動畫是主體，圖片是輔助。每支片 **3–5 張**就夠了。放太多會變成投影片，線稿講的原理反而被搶走。

## 兩種來源，各有分工

| | 網路上的真實照片 | Codex 生成的示意圖 |
|---|---|---|
| 用途 | **證據**：「這真的存在／有人做過」 | **氣氛**：開場、收尾，或還不存在、拍不到的畫面 |
| 例子 | 先例車款、NASA 的歷史照片、實驗裝置 | 車子倒掛在環形軌道上、懸浮的跑車 |
| 腳本 | `scripts/find_images.py search / get` | `scripts/codex_images.py`（讀 `gen_prompts.json`） |
| 畫面處理 | `duotone`：轉成背景色和主色兩色，融進片子的配色，強調色留給重點 | `keep`：生成時就照主題配色，最多稍微壓暗 |
| 擺法 | `card`：證據卡，旁邊附說明和來源 | `background`：整個畫面的背景，壓低透明度（0.4–0.5） |
| 畫面標示 | 一定要寫作者、授權、來源 | 一定要寫「AI 生成示意圖」 |

## 授權規則（硬性）

- 只能用**公有領域、CC0、CC BY、CC BY-SA**。`find_images.py` 會自動擋掉 NC、ND 和其他授權。
- CC BY-SA：裁切或套色後的版本也必須維持 CC BY-SA，`CREDITS.md` 和畫面上的來源都要寫清楚。
- **不用品牌官方的新聞照、宣傳圖、logo**，也不用沒有授權資訊的網路圖片（搜尋引擎找到的圖預設都不能用）。
- 照片裡有路人、其他品牌的 logo 或浮水印，要裁掉，或換一張。
- NASA 的照片多半是公有領域，但還是要用 `find_images.py` 確認那一張的授權。

## 生成圖規則

- 每個 prompt 都會自動加上：不能有品牌、logo、文字，要寫實、高對比，並套用主題的背景色和強調色。
- 主角如果是真實的產品（例如某品牌的車），生成「同類型但沒有品牌」的示意，**不要模仿那個產品的外型**。
- 構圖要留空白給文字（例如右邊三分之一或上半部留暗），在 prompt 裡寫明。
- 拿到圖之後**一定要親眼看**：有沒有冒出文字、logo、畸形的地方。不合格就刪掉那張 PNG，重跑 `codex_images.py`，已經存在的圖會跳過。

## 擺放（`images.json` 的 `placements`）

1. 先看每一格「落定後」的畫面（用 review-loop 的 contact sheet），找出**真的空著的區域**，記下 x、y、寬、高（1920×1080 座標）。不要蓋住線稿或標籤。
2. **證據卡**：放在那一格的停留段，也就是旁白講完重點、畫面靜止的時候。出現時間（`at`）放在最後一個子句開始的時候，或稍早一點。
   - 下面空間不夠：用 `"label_side": "right"`，文字放在圖片右邊。
3. **背景圖**：`after` 填該格背景圖層的 id，背景圖才會疊在網格上、內容下面。透明度大約 0.4–0.5。
   - 畫面上本來有一樣東西的線稿（例如同一台車）：用 `"hide": ["<線稿 id>"]` 和 `"hide_at": 0` 把它藏起來，不要讓兩台車疊在一起。
4. 背景圖的「AI 生成示意圖」字樣放在右上角（`top: 72px`），不要蓋住右下角的頁碼。

## 執行順序

```bash
python <me>/scripts/find_images.py search "<關鍵字>"
python <me>/scripts/find_images.py get "File:<檔名>" --name <短名> --project .
python <me>/scripts/codex_images.py --project .            # 讀 gen_prompts.json
python <me>/scripts/treat_images.py --project .            # 讀 images.json：裁切、套色 -> assets/images/treated/
python <me>/scripts/theme.py --project .                   # 三色＋字型（會從配色前的原始檔重做，所以圖片要在它之後放）
python <me>/scripts/place_images.py --project .            # 放進每一格，可重複執行
hyperframes check                                     # 照片上的文字對比度、重疊
python <me>/scripts/subset_fonts.py --project .            # 最後：圖說和來源也有字，瘦身要放在它們之後
```

## 實戰（Tesla Roadster 範例片）

- 開場：生成「車子倒掛在環形軌道上」當背景，透明度 0.5，字疊在上面依然清楚，對比度全部通過。
- 第 3 格（倒掛原理）：McMurtry Spéirling 的照片（CC BY-SA 4.0，作者 Calreyn88）當證據卡，標「真的做得到」。
- 第 5 格（冷氣推進器）：NASA 1984 年的載人機動裝置照片（公有領域），標「老前輩」。
- 收尾：生成「懸浮的跑車」當背景，同時把原本的小線稿車藏起來。
- 踩過的坑：
  - `codex exec` 在背景執行時，stdin 沒關會一直卡在等輸入。腳本已經改成關閉 stdin。
  - Spéirling 那張第一次裁太緊，把尾翼切掉了。
  - 背景圖的來源字樣和頁碼重疊。
  - 證據卡貼到路面線上了。
  - 這些都是在 `hyperframes check` 或 contact sheet 上抓到的。
