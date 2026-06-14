"""pytest 共通設定。

views/connection をインポートするには Django の設定読み込みと
DATABASE_URL 等の環境変数が必要になる。実 DB へは接続しない
（SQLAlchemy の create_engine は遅延接続で、本テストは DB を使う
処理を一切呼ばないため）が、import 時点で環境変数が要求されるので
ここでダミー値を注入してから django.setup() を行う。
"""
import os
import sys
from pathlib import Path

import django

# backend/ をインポートパスに追加（api・database・config を解決するため）
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# settings.py / connection.py が import 時に要求する環境変数。
# load_dotenv() は既存の環境変数を上書きしないため、ここで先に設定すれば
# .env の実値ではなくダミー値が使われ、テストがホスト環境に依存しない。
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()