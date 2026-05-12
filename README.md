# Thread Weaver

把一篇文章（Medium、個人 blog、或自己的 Markdown）整理成適合 Threads 閱讀的串文，經人工預覽確認後再發佈。

**這個工具做什麼**

- 讀取一篇文章 → AI 改寫成 2～4 篇 Threads 串文 JSON → 人工 preview → 串接 Threads Graph API 發文

**這個工具不做什麼**

- 不會自動爬你的 Medium 帳號全部文章
- 不會自動排程發文（只發「現在這一篇」）
- 不會自己決定要發什麼，整理規則寫在 [`AGENTS.md`](AGENTS.md)，由你帶任何 AI 工具執行

**誰適合用**

寫長文（Medium / Substack / 個人 blog）後想經營 Threads 但懶得手動切串文的人。

---

## 一張圖看懂

```text
文章來源
  │  (a) Medium URL → scripts/import_medium.py
  │  (b) 自己寫好的 Markdown
  ▼
drafts/article.md  (+ assets/ 若有圖)
  │
  ▼
你選一條路徑跑 AI（讀 AGENTS.md 規則）
  │  - Claude Code
  │  - Codex CLI / Cursor / Aider
  │  - 網頁版 ChatGPT / Claude.ai（手動模式）
  ▼
output/threads_draft.json
  │
  ▼
scripts/check_draft.py  ←  驗證字數、圖片存在
scripts/render_preview.py  ←  產 output/preview.md
  │
  ▼
人工 review
  │
  ▼
scripts/post_threads.py  ←  Threads Graph API 發文
```

---

## 前置需求

最低需求：

- Python 3.10+
- 一組 Threads Graph API 的 `user_id` 與 long-lived access token（取得方式：[docs/SETUP_THREADS.md](docs/SETUP_THREADS.md)）

若你要：

- **發圖片貼文** → 需要一個圖床（預設用 AWS S3；理由見 [`DECISIONS.md`](DECISIONS.md) D-001）
- **匯入 Medium 文章** → 需要 Ruby 3.3.6 + [`ZMediumToMarkdown`](https://github.com/ZhgChgLi/ZMediumToMarkdown)
- **純文字串文** → S3 / Ruby 都不需要

---

## 安裝

```bash
git clone https://github.com/<your-username>/thread-weaver.git
cd thread-weaver

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# 編輯 .env 填入 THREADS_USER_ID / THREADS_ACCESS_TOKEN
# 若要發圖再填 S3 三個欄位
```

---

## Quick Start

### 1. 準備一篇文章

任選一種：

**A. 自己寫 Markdown**

直接把文章放到 `drafts/article.md`。若有本機圖片，放到 `assets/<任意 id>/xxx.png`，
Markdown 內用相對路徑引用：

```markdown
![圖說](../assets/my-article/screenshot.png)
```

**B. 從 Medium 匯入**（需要 Ruby + ZMediumToMarkdown）

```bash
python3 scripts/import_medium.py "<MEDIUM_URL>"
```

完成後 `drafts/article.md` 與 `assets/<post_id>/` 會就位。

> 注意：`import_medium.py` 會清掉舊的 `drafts/article.md`、`output/threads_draft.json`、`output/published_result.json`，重跑前請確認上一輪已經發完文。

### 2. 用 AI 產生 Threads draft

整理規則寫在 [`AGENTS.md`](AGENTS.md)（和 [`CLAUDE.md`](CLAUDE.md) 內容相同，相容不同 CLI）。
任選一條路徑：

**路徑 1：Agentic CLI（推薦，有付費訂閱者）**

在 repo 根目錄啟動你的 CLI：

```bash
claude          # Claude Code (讀 CLAUDE.md)
codex           # Codex CLI    (讀 AGENTS.md)
cursor-agent    # Cursor CLI   (讀 AGENTS.md)
```

對它說：

> 請依照規則檔（AGENTS.md 或 CLAUDE.md），讀取 `drafts/article.md`，
> 重新產生 `output/threads_draft.json`。先不要發文。

**路徑 2：網頁免費版（零 API 費用）**

把 [`AGENTS.md`](AGENTS.md) 整份內容貼到 ChatGPT / Claude.ai / Gemini 免費版，
接著貼上 `drafts/article.md` 內容，要求它輸出符合規格的 JSON。
拿到 JSON 後手動存到 `output/threads_draft.json`。

### 3. 檢查 draft

```bash
python3 scripts/check_draft.py
```

會驗證：每篇字數 ≤ 430、`topic_tag` 存在、圖片路徑實際存在。

### 4. 產生 preview

```bash
python3 scripts/render_preview.py
```

打開 `output/preview.md` 人工 review。**這一步是發文前最後的把關，請不要跳過。**

### 5. 發文

```bash
python3 scripts/post_threads.py
```

成功後會寫出 `output/published_result.json`。

---

## S3 圖片上傳（可選）

Threads Graph API 不接受 `miro.medium.com` 等外站圖片，所以本機圖片必須先上傳到一個 public URL 才能發。預設方案是 AWS S3，理由見 [`DECISIONS.md`](DECISIONS.md) D-001。

**如果你只發純文字串文，可以完全跳過這段，S3 三個 env 留空即可。**

若你要發圖：

1. 建一個 public-read 的 S3 bucket
2. 在 `.env` 填入 `AWS_REGION` / `S3_BUCKET` / `S3_PUBLIC_BASE_URL`
3. 確保本機已設好 AWS CLI 認證或 IAM key

> 其他圖床（Cloudflare R2、Imgur 等）目前不支援，但 `scripts/post_threads.py` 裡的 `upload_local_file_to_s3()` 是單一函式，要替換不難。歡迎 PR。

---

## 專案結構

```text
thread-weaver/
├── AGENTS.md             # AI 助理整理規則（給 Codex / Cursor / 任何 agent）
├── CLAUDE.md             # 同上，內容相同（給 Claude Code）
├── README.md             # 你正在看這個
├── DECISIONS.md          # 架構與設計決策的「為什麼」
├── RUNBOOK.md            # 維運、debug、常見問題
├── LICENSE               # MIT
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   └── SETUP_THREADS.md  # Threads token 取得指引
├── examples/             # 範例輸入輸出
├── scripts/              # Pipeline 腳本
├── drafts/               # 你的草稿（.gitignored）
├── assets/               # 你的圖片（.gitignored）
└── output/               # 衍生輸出（.gitignored）
```

---

## 重要：版權與 ToS

- 本工具僅供整理「你自己擁有版權的文章」。請勿用來轉發他人作品。
- 使用 Medium 匯入功能請遵守 [Medium Terms of Service](https://policy.medium.com/medium-terms-of-service-9db0094a1e0f)。
- 使用 Threads Graph API 請遵守 [Meta Platform Terms](https://developers.facebook.com/terms/) 與 Threads 平台政策。
- 若你的文章內含他人圖片（截圖、引用圖等），上傳前請確認授權狀態。

---

## 相關文件

| 文件 | 用途 |
|------|------|
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | AI 助理整理規則（兩份內容相同）|
| [`docs/SETUP_THREADS.md`](docs/SETUP_THREADS.md) | Threads token 怎麼拿 |
| [`DECISIONS.md`](DECISIONS.md) | 架構決策的「為什麼」 |
| [`RUNBOOK.md`](RUNBOOK.md) | 維運、debug、常見問題 |
| [`examples/`](examples/) | 範例輸入輸出 |

---

## License

[MIT](LICENSE)
