#!/bin/sh

cd '/home（manage.pyがあるディレクトリのパス）'

# 期限切れのセッションを削除する
/usr/bin/python3 manage.py clearsessions
# 期限切れのAPIトークンを削除する
/usr/bin/python3 manage.py flushexpiredtokens
