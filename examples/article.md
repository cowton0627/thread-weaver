# 用 Claude Code 整理一週 PR 的心得

> 這是一個假的範例文章，用來示範 `threads-publisher` 的輸入輸出格式。

## 起因

每週固定要回顧團隊的 PR，原本要花一兩個小時。
最近開始試著用 Claude Code 幫忙整理，發現幾個關鍵小技巧。

## 解法

我設計了一個 prompt 模板，把 PR 列表丟給 Claude Code，請它：

1. 依照影響範圍分類
2. 標出需要 follow-up 的項目
3. 自動產生對外的 weekly digest 草稿

關鍵在於：**不要要求它直接「總結所有 PR」**，而是要它先分群、再分群內精簡，
最後才合成 digest。一步步分解任務的效果遠比一句話請它「幫我寫週報」好。

## 踩坑提醒

- 不要把整個 repo 都餵給它，挑相關目錄即可
- 對 generated 檔（lock file、build artifacts）要明確排除
- 結果一定要人工 review 一遍，特別是「誰負責什麼」這種敘述

## 結語

這個流程讓我從每週 90 分鐘降到 20 分鐘，省下的時間拿來寫文章剛剛好。

完整 prompt 模板與細節我寫在 Medium：<https://medium.com/example/weekly-pr-digest>
