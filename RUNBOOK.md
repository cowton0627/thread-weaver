# RUNBOOK

本文件記錄：

* 維運流程
* 常見問題
* Threads API quirks
* debug 方法
* operational tuning
* 容易踩坑的地方

不記錄架構理由（請看 `DECISIONS.md`）。

---

# 啟動環境

```bash
source venv/bin/activate          # Windows: venv\Scripts\activate
```

確認：

```bash
which python3
```

應指向 repo 內的 `venv/bin/python3`。

---

# 基本工作流

完整步驟見 `README.md` 的 Quick Start。本文件只記錄出錯時要看的東西。

* `import_medium.py` 會清掉舊的 draft / preview / publish result，重跑前要確認上一輪已經完成
* `post_threads.py` 成功後會寫出 `output/published_result.json`

---

# 常見問題

## 問題：Threads API 拒絕圖片

原因：`miro.medium.com` 等外站圖片 URL 常被 Threads API 拒絕。

解法：

一定要走 `本機圖片 → S3 → public URL → Threads API`，不要直接用 Medium 圖片網址。
詳見 `DECISIONS.md` D-001。

---

## 問題：AI 編造圖片

症狀：`local_image_path` 指向的檔案不存在。

解法：

* 圖片只能引用 Markdown 中已存在的圖片
* 不允許自由產生 `image_url`
* 用 `python3 scripts/check_draft.py` 驗證

---

## 問題：字數超過限制

目前限制：

| 層級 | 限制 |
|------|------|
| `AGENTS.md` / `CLAUDE.md` 規則 | 450 |
| `check_draft.py` 驗證 | 430 |
| Threads API 實際上限 | 500 |

原則：

* AI 目標控制在 430 左右
* 不要手動亂切句子
* 超過時請 AI 重寫

---

## 問題：Threads publish fail

常見原因：

* container 建立後太快 publish
* 圖片尚未可存取
* `topic_tag` 格式不合法

目前 `post_threads.py` 內的 sleep 值：

```python
sleep(8)   # create container → publish
sleep(3)   # carousel items 之間
sleep(5)   # post 之間
```

這是試錯後較穩定的值，不是官方保證。不要隨便調小。

---

## 問題：Long-lived token 過期

Threads long-lived access token 60 天有效。到期前用 refresh endpoint 延長：

```bash
curl "https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=<CURRENT_TOKEN>"
```

更新 `.env` 內的 `THREADS_ACCESS_TOKEN`。

---

# Operational Tuning

## sleep timing

| 行為 | sleep |
|------|-------|
| create → publish | 8 秒 |
| carousel items | 3 秒 |
| post 間隔 | 5 秒 |

原因：Threads container 建立後不能立刻 publish。這是實測穩定值，不是官方保證值。

---

# `.env` 規則

`.env`：

* 不應 commit（已在 `.gitignore`）
* 不應貼到聊天紀錄
* 不應給 AI 助理讀取

必要時：

* 只檢查欄位名稱
* 不輸出 token

---

# Debug Checklist

發文失敗時：

## 1. 先檢查 `.env`

確認 `THREADS_USER_ID`、`THREADS_ACCESS_TOKEN` 存在；若發圖，再加 `S3_BUCKET` 等。

## 2. 檢查 draft

```bash
python3 scripts/check_draft.py
```

## 3. 檢查 preview

```bash
python3 scripts/render_preview.py
```

確認：圖片存在、排版正常、`topic_tag` 正常。

## 4. 測試 S3（若有設）

直接寫一個 boto3 上傳測試：

```bash
python3 -c "
import boto3, os
from dotenv import load_dotenv
load_dotenv()
s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
print(s3.list_buckets()['Buckets'])
"
```

能列出 bucket 表示認證 OK。

## 5. Retry

Threads API 偶爾不穩。先 retry 一次再判定問題。

---

# 未來可能擴充

目前尚未實作：

* retry queue
* scheduled publish
* multi-platform publisher
* analytics
* automatic hook review
* AI topic optimization
* multi-agent review
* 替代圖床（Cloudflare R2 / Imgur）
