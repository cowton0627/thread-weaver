# 取得 Threads Graph API 認證

> 本文是「個人開發者最小可行路徑」的高階指引。Meta 文件改版頻繁，下面的順序若失效，請以 [官方文件](https://developers.facebook.com/docs/threads/) 為準。

## 你需要拿到的兩個值

填到 `.env`：

```env
THREADS_USER_ID=
THREADS_ACCESS_TOKEN=
```

- `THREADS_USER_ID`：你的 Threads 帳號的 numeric ID（不是 handle）
- `THREADS_ACCESS_TOKEN`：long-lived access token（60 天有效，到期前可 refresh）

---

## 大致步驟

1. **註冊 Meta for Developers 帳號** 
   <https://developers.facebook.com/>

2. **建立一個 App** 
   選「Other」→「Business」類型。

3. **加入 Threads API 產品** 
   在 App Dashboard 找到「Add Products」→ 啟用「Threads API」。

4. **設定 redirect URI** 
   個人開發暫時可以填 `https://localhost/`，反正不會真的跑 OAuth callback。

5. **走一次 OAuth flow 拿 short-lived token** 
   組這個 URL 並用瀏覽器開：

   ```text
   https://threads.net/oauth/authorize
     ?client_id=<YOUR_APP_ID>
     &redirect_uri=<YOUR_REDIRECT_URI>
     &scope=threads_basic,threads_content_publish
     &response_type=code
   ```

   登入後會被導回 `redirect_uri?code=...`，把那個 `code` 抓下來。

6. **用 code 換 short-lived token** 
   參考官方文件，POST 到 `https://graph.threads.net/oauth/access_token`。

7. **把 short-lived token 換成 long-lived token** 
   60 天有效，本工具用的是這個：

   ```text
   GET https://graph.threads.net/access_token
     ?grant_type=th_exchange_token
     &client_secret=<YOUR_APP_SECRET>
     &access_token=<SHORT_LIVED_TOKEN>
   ```

8. **撈 user_id** 

   ```bash
   curl "https://graph.threads.net/v1.0/me?fields=id,username&access_token=<LONG_LIVED_TOKEN>"
   ```

   回傳的 `id` 就是 `THREADS_USER_ID`。

---

## 注意事項

- App 在「Development」模式下只能用「已加入測試的帳號」發文，這對個人自用已經夠。
- 要讓其他人也能用你的 App，需要走 Meta App Review，門檻較高，個人專案通常不需要。
- Long-lived token 到期前可以呼叫 refresh endpoint 延長：

  ```text
  GET https://graph.threads.net/refresh_access_token
    ?grant_type=th_refresh_token
    &access_token=<LONG_LIVED_TOKEN>
  ```

- **永遠不要 commit `.env`。** 已經在 `.gitignore` 內排除。

---

## 我卡關了

- 官方參考文件：<https://developers.facebook.com/docs/threads/>
- 開 issue 描述卡在哪一步，附上錯誤訊息（**請先把 token 遮掉**）。
