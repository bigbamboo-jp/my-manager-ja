# 独自の例外クラスをまとめたモジュール
# エラーコード：クラス名のCRC32ハッシュ値（生成サイト：http://kujiira.com/tools/hash）

class UnknownError(Exception):
    # 原因を特定できないエラー
    def __init__(self):
        self.error_code = '28cda50c'


class InputValueValidationError(Exception):
    # 入力式質問で入力された値が不正である場合に発生する
    def __init__(self):
        self.error_code = 'fa4d94da'


class OtherServiceHaveNoUserError(Exception):
    # 他のサービス上に必要なユーザーが存在しなかった場合に発生する
    def __init__(self):
        self.error_code = '72059f11'


class OtherServiceHaveNoAttendanceRecordError(Exception):
    # 他のサービス上に必要な出席記録が存在しなかった場合に発生する
    def __init__(self):
        self.error_code = 'dbf5528f'


class OtherServiceAuthenticationError(Exception):
    # 他のサービスの認証情報が無効である場合に発生する
    def __init__(self):
        self.error_code = 'b1db2ef0'


class OtherServiceInvalidPermissionsError(Exception):
    # 他のサービスでの権限が不足している場合に発生する
    def __init__(self):
        self.error_code = '89339d3b'


class OtherServiceFieldNameError(Exception):
    # 他のサービスに指定された名前のフィールドが見つからなかった場合に発生する
    def __init__(self):
        self.error_code = '85c57850'


class OtherServiceTableNotFoundError(Exception):
    # 他のサービスに指定されたテーブル・ベースが見つからなかった場合に発生する
    def __init__(self):
        self.error_code = 'e1806d3a'


class CustomizationError(Exception):
    # カスタマイズ用の関数で問題が起きた場合に発生する
    def __init__(self, original_exception: Exception):
        self.error_code = '	ae9455cc'
        self.original_exception = original_exception
