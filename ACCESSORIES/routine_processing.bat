@echo off

cd 'C:\home（manage.pyがあるディレクトリのパス）'

rem 期限切れのセッションを削除する
python3 manage.py clearsessions
rem 期限切れのAPIトークンを削除する
python3 manage.py flushexpiredtokens
