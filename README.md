# マイマネージャー
チームメンバーそれぞれの作業時間とメンタルの状態を記録することができるウェブアプリ

<img src="homepage.png" width="1000">

## このアプリケーションの種類について
マイマネージャーはDjangoで開発されたウェブアプリ（ウェブブラウザ上から利用するアプリケーション）です。  
オープンソースなので自分好みにカスタマイズしてサービスを提供することができます。
## このアプリケーションでできること
- ウェブブラウザから出席時・退席時に打刻をする
- 自分の過去1年間の出席記録を確認する
- Airtableと連携して、各メンバーの出席状況を視覚的に確認したり、記録をCSVファイルにエクスポートしたり、API経由で他サービスと組み合わせる
- 打刻をする際に予め用意された質問に答えることによってメンタルの状態を自動的に判定する
- システムに記録されたデータに基づいて一人一人にメンタルヘルスについてのレポートを表示する（それによって過労などを防止する）
- PC用拡張機能を活用して記録のし忘れを防止したり、退席時間についてのリマインダーを表示する
## 使い始める
**前提条件：Python 3.12以上、PostgreSQL 16以上がインストール済みであること**
1. 下のリンクから最新のプログラムファイルをダウンロードして、データを解凍してください。  
[https://github.com/bigbamboo-jp/my-manager-ja/releases](https://github.com/bigbamboo-jp/my-manager-ja/releases)
1. config/`settings.py`にデータベース（PostgreSQL）とAirtable（オプション）の認証情報を書き込んでください。  
    **Airtableとの連携について**  
    このアプリケーションでAirtableのベースを読み書きするにはテーブル名・列名の設定も行う必要があります。  
    ※以下のリンク先のテンプレートを使用する場合は設定不要です（Copy base ボタンを押すとコピーできます）。  
    [https://airtable.com/shrRCYwNlHhpOvfbw](https://airtable.com/shrRCYwNlHhpOvfbw)
1. `manage.py`があるディレクトリで以下のコマンドを実行してください。
    ```
    python -m venv .venv

    # Windowsの場合（PowerShellを使用する場合の手順）
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    .venv\Scripts\Activate.ps1
    
    # macOSまたはLinuxの場合
    source djangox/bin/activate
    ```
1. プロンプトの前に **(.venv)** が表示されていることを確認して、以下のコマンドを実行してください。
    ```
    (.venv) $ pip install -r requirements.txt
    (.venv) $ python manage.py migrate
    (.venv) $ python manage.py createsuperuser
    (.venv) $ python manage.py runserver
    # Starting development server at http://127.0.0.1:8000/
    ```
1. ウェブブラウザで[http://127.0.0.1:8000/](http://127.0.0.1:8000/)にアクセスするとアプリケーションを使用できます。
> 参考：サイト名の変更などは管理サイト（[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)）で行うことができます。
## 定期処理のスケジューリング
プログラムファイルの中に定期的に行うべき処理を記述したスクリプトが付属しています。  
実際にサービスを提供する際は、スクリプトファイルにプログラムファイルがあるディレクトリのパスを書き込んだ後、Windowsの場合はタスクスケジューラに、macOS・Linuxの場合はcronに登録してください。  
※使用するスクリプトは、Windowsの場合は`routine_processing.bat`、macOS・Linuxの場合は`routine_processing.sh`です。
## PC用拡張機能
このアプリケーションはWindows専用ソフトウェア「My Manager Extension」と組み合わせることでより便利に使うことができます。  
「My Manager Extension」について、詳しくは以下のページをご覧ください。  
[https://github.com/bigbamboo-jp/my-manager-extension-ja](https://github.com/bigbamboo-jp/my-manager-extension-ja)
## ライセンス
このプロジェクトは[DjangoX](https://github.com/wsvincent/djangox)をベースに開発されました。  
そのため、このプロジェクトにはDjangoXのライセンス（[LICENSE](LICENSE)）とマイマネージャーのライセンス（[MY MANAGER LICENSE](MY%20MANAGER%20LICENSE)）の両方が適用されます。  
※内容が相違している部分についてはDjangoXのライセンス事項が優先されます。