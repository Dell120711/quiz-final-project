# 資料結構雜湊表測驗網站

本專案使用 Django 製作資料結構「雜湊表」章節的線上測驗系統。系統包含登入、註冊、題庫後台管理、隨機出題、隨機選項排列、即時回饋、作答紀錄與排行榜。

## 系統需求

- Python 3.13
- Django 6.0.5
- SQLite

## 使用 Conda 建立環境

教學團隊可在專案根目錄執行：

```bash
conda env create -f environment.yml
conda activate hash-quiz
```

確認 Django 版本：

```bash
python -m django --version
```

## 初始化資料庫

建立環境後，進入專案根目錄執行：

```bash
python manage.py migrate
```

若需要登入 Django Admin，請建立管理員帳號：

```bash
python manage.py createsuperuser
```

## 執行網站

啟動開發伺服器：

```bash
python manage.py runserver
```

開啟瀏覽器進入：

```text
http://127.0.0.1:8000/
```

未登入時會先進入登入頁。一般學生可透過註冊頁建立帳號。

## 後台管理

管理員後台網址：

```text
http://127.0.0.1:8000/admin/
```

只有管理員帳號可以看到後台入口。後台可新增、修改、刪除題目與選項。

本專題章節固定為「雜湊表」，因此後台不提供新增章節功能。新增題目時系統會自動歸到雜湊表章節。

新增選項時只需要輸入選項文字，不需要輸入 A/B/C/D。測驗時系統會隨機排列選項，並依照當下順序顯示 A、B、C、D、E。

## 主要功能

- 使用者登入與註冊
- 管理員題庫管理
- 固定雜湊表章節測驗
- 測驗題數可選 5 或 10 題
- 題目順序隨機
- 選項順序隨機
- 作答後立即顯示正確答案
- 測驗總結顯示使用者答案與正確答案
- 作答紀錄顯示每次測驗成績與作答明細
- 排行榜顯示每位使用者最高成績
- 錯題狀態保留於程式內，用於之後優先安排錯題

## 專案結構

```text
finalproject/
├── manage.py
├── db.sqlite3
├── README.md
├── environment.yml
├── quiz/
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
└── quiz_site/
    ├── settings.py
    └── urls.py
```
