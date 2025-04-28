import argparse
import asyncio
import sys
from .config import Config
from .crawler import LinkChecker
from .reporter import generate_report

def parse_args():
    parser = argparse.ArgumentParser(
        description="リンク切れチェックスクリプト (CLI)"
    )
    parser.add_argument(
        "start_url",
        help="起点URL"
    )
    parser.add_argument(
        "-o", "--output",
        default="report.html",
        help="出力HTMLレポートのファイルパス (default: report.html)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--same-origin",
        dest="mode",
        action="store_const",
        const="same",
        help="同一オリジンのみ (default)"
    )
    group.add_argument(
        "--include-subdomains",
        dest="mode",
        action="store_const",
        const="sub",
        help="サブドメインを含む"
    )
    parser.set_defaults(mode="same")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="最大クロール深度 (default: 3, -1 for unlimited)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="除外URLパターン (部分文字列マッチ、複数指定可)"
    )
    parser.add_argument(
        "--include",
        dest="include",
        action="append",
        default=[],
        help="包含URLパターン (部分文字列マッチ、複数指定可)"
    )
    parser.add_argument(
        "--check-resources",
        action="store_true",
        help="リソースリンクもチェック (img, link, script)"
    )
    parser.add_argument(
        "--user-agent",
        default="href-hound/1.0",
        help="User-Agent文字列 (default: href-hound/1.0)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="タイムアウト（秒、default: 10.0）"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="同時リクエスト数 (default: 5)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="リクエスト間隔（秒、default: 0.0）"
    )
    parser.add_argument(
        "--error-codes",
        default="",
        help="リンク切れ判定HTTPステータスコード (カンマ区切り)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    mode = args.mode
    same_origin = (mode == "same")
    include_subdomains = (mode == "sub")
    if args.error_codes:
        try:
            error_codes = [int(x) for x in args.error_codes.split(",") if x.strip()]
        except ValueError:
            print("error-codes must be comma-separated integers", file=sys.stderr)
            sys.exit(1)
    else:
        error_codes = []

    config = Config(
        start_url=args.start_url,
        output=args.output,
        same_origin=same_origin,
        include_subdomains=include_subdomains,
        max_depth=args.max_depth,
        exclude=args.exclude,
        include=args.include,
        check_resources=args.check_resources,
        user_agent=args.user_agent,
        timeout=args.timeout,
        concurrency=args.concurrency,
        delay=args.delay,
        error_codes=error_codes
    )

    try:
        checker = LinkChecker(config)
        results = asyncio.run(checker.run())
        generate_report(results, config.output)
        print(f"Report generated: {config.output}")
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()