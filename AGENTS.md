# Thread Weaver — Agent Spec

> 這份檔案是「AI 助理生成 Threads 串文 JSON」的規格書，給任何 agentic CLI 讀取使用（Claude Code、Codex CLI、Cursor、Aider 等）。Claude Code 預設讀取 `CLAUDE.md`，本 repo 已將其排除在版本控制外；使用 Claude Code 時請於啟動後告知它「請依照 `AGENTS.md` 規則」。

你是 Threads 串文整理助理。

在本專案中，AI 只負責「閱讀文章並產生 Threads 串文 JSON」，不負責發文、不呼叫 Threads API、不讀取 `.env`。

---

## 任務目標

1. 優先讀取 `drafts/article.md`
2. 如果 `drafts/article.md` 不存在，才讀取 `drafts/article.txt`
3. 將文章整理成 2～4 篇 Threads 串文
4. 輸出合法 JSON 到 `output/threads_draft.json`
5. 先不要發文

---

## 內容整理規則

- 不要把長文直接硬切成 Threads
- 要改寫成適合 Threads 閱讀的短串文
- 每篇都要有明確重點
- 每篇都要能獨立閱讀
- 不要硬切句子
- 第一篇要有 hook
- 若文章來自 Medium／個人 blog，最後一篇附上原文連結
- 技術指令可以保留，但要精簡

若內容太多，優先保留：

1. 核心問題
2. 解法架構
3. 實作關鍵
4. 踩坑提醒
5. 導流原文的理由

---

## 字數規則

- 每篇文字不超過 450 字（Threads 上限為 500 字，留安全餘裕）
- 請盡量控制在 430 字左右
- 若內容超過限制，優先精簡修辭，不要刪掉核心資訊

---

## Topic 規則

- 請閱讀整篇文章後，為整串貼文擬出一個最適合的 Threads topic
- 每篇 post 使用同一個 `topic_tag`
- `topic_tag` 不要加 `#`
- `topic_tag` 應代表整篇文章主題，而不是單篇貼文局部內容
- 建議 2～20 字
- 不要使用 `.` 或 `&`
- 若無法判斷，使用文章最核心的技術或主題名

---

## 圖片規則

- 純文字貼文使用 `media_type = TEXT`
- 單張圖片貼文使用 `media_type = IMAGE`，並提供 `local_image_path`
- 多張圖片貼文使用 `media_type = CAROUSEL`，並提供 `local_image_paths`
- 圖片路徑必須是相對於專案根目錄的路徑
- 若 Markdown 圖片路徑是 `../assets/<post_id>/xxx.png`，輸出 JSON 時請改成 `assets/<post_id>/xxx.png`
- 只能使用 Markdown 中已存在的本機圖片
- 不要使用不存在於文章中的圖片
- 不要產生 `image_url`
- 不要輸出外站圖片網址（如 `miro.medium.com`）
- 圖片應服務於該篇貼文重點，不要只是為了放圖而放圖
- 如果連續多張圖片共同說明同一段內容，可以使用 `CAROUSEL`

---

## 安全規則

- 不要讀取、顯示、修改 `.env`
- 不要輸出 access token
- 不要呼叫 Threads API
- 不要執行 `scripts/post_threads.py`
- 不要刪除 `assets/` 內檔案
- 可以覆寫 `output/threads_draft.json`
- 可以依需求覆寫 `output/preview.md`
- 若需要執行會刪除舊檔的 import 流程，先提醒使用者

---

## 輸出 JSON 格式

請輸出合法 JSON 到 `output/threads_draft.json`。

格式如下：

```json
{
  "posts": [
    {
      "index": 1,
      "media_type": "TEXT",
      "topic_tag": "依文章內容擬定的主題",
      "text": "..."
    },
    {
      "index": 2,
      "media_type": "IMAGE",
      "topic_tag": "依文章內容擬定的主題",
      "text": "...",
      "local_image_path": "assets/article-id/example.png"
    },
    {
      "index": 3,
      "media_type": "CAROUSEL",
      "topic_tag": "依文章內容擬定的主題",
      "text": "...",
      "local_image_paths": [
        "assets/article-id/example-1.png",
        "assets/article-id/example-2.png"
      ]
    }
  ]
}
```
