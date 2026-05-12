# Thread Weaver — 設計決策紀錄

本文件記錄：

* 架構決策
* workflow 邊界
* 長期設計理由
* trust boundary
* 未來維護時仍重要的「為什麼」

不記錄：

* operational tuning
* sleep 數值
* 一次性 workaround
* debug 步驟
* 日常操作流程

那些請放在 `RUNBOOK.md`。

---

# D-001 圖片走 S3，不直接使用外部圖片 URL

背景：

Threads Graph API 對圖片來源有限制。Medium 原始圖片（`miro.medium.com`）常被拒絕，外部圖片來源也不可控。

決定：

所有圖片統一走：

```text
本機圖片 → AWS S3 → public URL → Threads API
```

S3 bucket 內以 `threads-assets/<uuid>-<filename>` 方式儲存。

理由：

* 避免 Threads API 拒絕外站圖片
* 統一圖片來源
* 避免 Medium hotlink 問題
* 發文流程更 deterministic
* 未來可擴充 CDN / cache policy

未解：

* 未來是否改成 CloudFront
* 是否需要圖片壓縮 pipeline
* 是否需要自動清理舊 assets
* 是否要支援 Cloudflare R2 / Imgur 等其他圖床（見 D-007）

---

# D-002 使用 ZMediumToMarkdown 作為匯入 pipeline

背景：

要把 Medium 長文完整本機化，包括 Markdown、圖片、文章結構。

決定：

使用 [ZMediumToMarkdown](https://github.com/ZhgChgLi/ZMediumToMarkdown) 作為第一階段 import tool。

流程：

```text
Medium URL
→ ZMediumToMarkdown
→ output/zmediumtomarkdown/
→ import_zmedium.py
→ drafts/article.md + assets/
```

理由：

* 可完整保留文章內容
* 可下載圖片資產
* Markdown 結構穩定
* 比手動複製更可重複
* 可 script 化

未解：

* Medium 結構變動時的相容性
* 是否要替換成自建 parser
* 是否支援其他平台（Substack / Hashnode）

---

# D-003 AI 只負責產 JSON，不直接發文

背景：

「內容改寫」與「實際發文」屬於不同性質的工作。

* 內容改寫需要：語意理解、摘要能力、Threads 語氣調整
* 發文涉及：token、API、retry、sleep timing、S3 upload、deterministic execution

決定：

AI 只負責：

```text
drafts/article.md → output/threads_draft.json
```

真正發文由 `scripts/post_threads.py` 負責。

理由：

* 降低 AI 誤發文風險
* 避免 AI 接觸 `.env`
* upload / retry 可程式化驗證
* draft 可先經過 check 與 preview
* 人工 review 可保留最後控制權

未解：

* 是否要加入 scheduled publish
* 是否要加入 retry queue
* 是否要支援 multi-platform publishing

---

# D-004 全篇串文共用同一個 topic_tag

背景：

Threads 每篇 post 都可以帶自己的 topic。若每篇使用不同 topic，容易讓整串內容失去一致性。

決定：

同一串 thread 的所有 post **共用同一個 `topic_tag`**。

topic 應代表：整篇文章主題、長期可搜尋主題、核心技術或概念；而不是單篇局部內容。

理由：

* 維持 thread 主題一致性
* 降低 topic fragmentation
* 提升搜尋與推薦穩定性
* 避免 AI 每篇亂換 topic

未解：

* 是否要加入 topic suggestion system
* 是否要建立 topic whitelist
* 是否要加入 analytics 驗證 topic 效果

---

# D-005 圖片必須引用本機已存在素材

背景：

若允許 AI 自由產生 `image_url`，可能出現：幻覺圖片、不存在檔案、外部 hotlink、使用 `miro.medium.com`、不可控來源。

決定：

AI：

* 只能使用 Markdown 中已存在圖片
* 必須輸出 `local_image_path` 或 `local_image_paths`
* 禁止輸出 `image_url`

並由 `scripts/check_draft.py` 額外驗證檔案實際存在。

理由：

* 建立 trust boundary
* 防止 hallucinated assets
* 保持發文 deterministic
* 避免外部依賴
* 提升 draft 可驗證性

未解：

* 是否要加入 image metadata validation
* 是否要支援 AI 自動選圖
* 是否要加入 image ranking

---

# D-006 專案採用「永久素材 vs 衍生產物」分層

背景：

Threads pipeline 會產生大量 preview、publish result、import output、cache 中介檔。若全部 commit，repo 會快速污染。

決定：

專案區分：

**永久素材（可追蹤）**：source code、文件、scripts

**衍生產物（不追蹤）**：publish result、cache、preview、import 中介輸出、使用者自己的 `drafts/` 與 `assets/`

由 `.gitignore` 控制。

理由：

* 保持 repo 乾淨
* 避免 commit 噪音
* 降低衍生檔污染
* 保持 pipeline 可重建

未解：

* 是否要定期清理 assets
* 是否要建立 release artifacts
* 是否需要 cache policy

---

# D-007 不綁特定 AI CLI，靠 AGENTS.md / CLAUDE.md 跨工具規格

背景：

最初版本在私有環境中假設使用 Claude Code。但開源後，使用者可能用 Codex CLI、Cursor、Aider，甚至完全沒有付費 LLM CLI、只想用 ChatGPT 免費版。

決定：

* AI 助理規格寫在 `AGENTS.md`（2025 年後逐漸成為跨工具慣例）
* 為了相容 Claude Code 預設讀取路徑，再放一份內容相同的 `CLAUDE.md`
* 不在 repo 內 hard-code 任何特定廠商 API 呼叫
* README 同時列出「Agentic CLI」與「網頁手動模式」兩條路徑

理由：

* 受眾從「會用 Claude Code 的人」放大到「會跑 Python 的人」
* 即使完全不付費也能用（網頁免費版手動模式）
* 跨工具 prompt 標準演進中，AGENTS.md 是目前最廣的共識
* 維護成本最低：只有一份規格，兩個檔案內容相同

代價：

* 兩份檔案要手動保持同步（已在檔頭加註提醒）
* 不同 AI 對同樣規格的執行結果會有差異，使用者需要自己 review

未解：

* AGENTS.md 慣例是否會穩定下來
* 是否要改用 symlink（Windows 相容性較差）
* 是否要在 CI 自動比對兩檔案內容是否一致

---

# D-008 S3 從必要降級為可選

背景：

初版要求所有使用者都要設 AWS S3，即使只發純文字串文。對個人使用者門檻過高（要開 AWS 帳號、設 IAM、設 bucket policy）。

決定：

* `post_threads.py` 只在偵測到 IMAGE 或 CAROUSEL 貼文時才檢查 S3 環境變數
* `boto3` 延遲到實際上傳時才 import
* `.env.example` 將 S3 三個欄位標示為「只在發圖時才需要」

理由：

* 純文字使用者零門檻
* 想發圖的使用者再花時間設 S3
* 維持「圖片走 S3」的決策（D-001），不改變圖片處理架構

未解：

* 是否要支援 Cloudflare R2、Imgur 等替代圖床
* 是否要把 uploader 抽象成 interface（目前只有單一函式 `upload_local_file_to_s3()`）
