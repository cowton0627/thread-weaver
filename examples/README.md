# Examples

這個資料夾示範 `thread-weaver` 的輸入與輸出長相，
讓你不用拿到 Threads token、不用設 S3，也能先看懂這個工具到底在做什麼。

## 檔案

- `article.md` — 假的輸入文章（一篇 Medium 風格的技術心得）
- `threads_draft.json` — 假的輸出 JSON（已切成 4 篇 Threads 串文）

## 如何用這份範例試跑

1. 複製 `examples/article.md` 到 `drafts/article.md`
2. 在 repo 根目錄跑你偏好的 AI CLI（Claude Code / Codex / Cursor）
3. 對 AI 說：「請依照 AGENTS.md，讀取 drafts/article.md，重新產生 output/threads_draft.json」
4. 跑 `python3 scripts/check_draft.py` 驗格式
5. 跑 `python3 scripts/render_preview.py` 看排版
6. 比較你 AI 產的版本跟 `examples/threads_draft.json` 的差異

注意：`threads_draft.json` 只是一份「合理的」輸出範例，不是「唯一正解」。
不同 AI、不同 prompt 設定、不同文章長度都會產出不同切法。
