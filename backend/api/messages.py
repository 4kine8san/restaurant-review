# ユーザー向けエラーメッセージ定数

# 汎用
ERR_SERVER          = "サーバーエラーが発生しました"
ERR_INVALID_INPUT   = "入力値が不正です"
ERR_INVALID_REQUEST = "リクエストが不正です"
ERR_INVALID_PARAMS  = "パラメータが不正です"

# レストラン
ERR_RESTAURANT_NOT_FOUND = "レストランが見つかりません"
ERR_RESTAURANT_NAME_REQUIRED = "店名は必須です"

# 写真
ERR_PHOTO_NOT_FOUND        = "写真が見つかりません"
ERR_PHOTO_RESTAURANT_ID    = "restaurant_id は必須です"
ERR_PHOTO_FILE_REQUIRED    = "photo ファイルが必要です"
ERR_PHOTO_INVALID_FILE     = "有効な画像ファイルを指定してください"
ERR_PHOTO_IDS_INVALID      = "photo_ids が不正です"

# マスタ
ERR_MASTER_NOT_FOUND = "マスタが見つかりません"

# 管理者
ERR_ADMIN_PASSWORD_WRONG   = "パスワードが不正です"
ERR_ADMIN_PASSWORD_NOT_SET = "管理者パスワードが設定されていません"

# 自動補完
ERR_AUTOFILL_BRAVE_KEY_NOT_SET  = "BRAVE_API_KEY が設定されていません"
ERR_AUTOFILL_GEMINI_KEY_NOT_SET = "GEMINI_API_KEY が設定されていません"
ERR_AUTOFILL_DAILY_QUOTA = (
    "Gemini API の1日の無料利用枠を使い切りました。"
    "翌日（日本時間 午後5時頃リセット）に再度お試しください。"
)
ERR_AUTOFILL_RATE_LIMIT = (
    "Gemini API のリクエスト制限に達しました。"
    "約1分待ってから再試行してください。"
)
ERR_AUTOFILL_FAILED = "自動補完に失敗しました"