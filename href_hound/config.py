from dataclasses import dataclass, field
from typing import List
import threading

@dataclass
class Config:
    # 起点URL
    start_url: str
    # 出力HTMLレポートのファイルパス
    output: str
    # クロール範囲: 同一オリジンのみ
    same_origin: bool = True
    # クロール範囲: サブドメインを含む
    include_subdomains: bool = False
    # 最大クロール深度 (-1 で無制限)
    max_depth: int = 3
    # 除外URLパターン（部分文字列マッチ）
    exclude: List[str] = field(default_factory=list)
    # 包含URLパターン（部分文字列マッチ）
    include: List[str] = field(default_factory=list)
    # リソースリンクもチェック
    check_resources: bool = False
    # User-Agent文字列
    user_agent: str = "LinkChecker/1.0"
    # タイムアウト（秒）
    timeout: float = 10.0
    # 同時リクエスト数
    concurrency: int = 5
    # リクエスト間隔（秒）
    delay: float = 0.0
    # リンク切れ判定ステータスコード
    error_codes: List[int] = field(default_factory=list)
    # 中断フラグ
    cancel_event: threading.Event = field(default_factory=threading.Event)