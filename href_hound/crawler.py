import asyncio
from typing import Optional, Callable
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from .config import Config


class LinkResult:
    """
    リンクチェック結果を表す。
    """
    def __init__(self, source: str, target: str,
                 status: Optional[int], error: Optional[str],
                 is_broken: bool):
        self.source = source
        self.target = target
        self.status = status
        self.error = error
        self.is_broken = is_broken


class LinkChecker:
    """
    リンク切れチェックのコアロジック。
    """
    def __init__(self, config: Config,
                 progress_callback: Optional[Callable[[int, int, str], None]] = None):
        self.config = config
        self.progress_callback = progress_callback
        self._visited = set()
        self._results: list[LinkResult] = []
        # キャッシュ: 同一リンクの重複チェック防止
        self._link_cache: dict[str, tuple[Optional[int], Optional[str], bool]] = {}
        # 起点URLホストとパスプレフィックスを記録
        parsed_start = urlparse(config.start_url)
        self._start_host = parsed_start.netloc
        # サブディレクトリ制限: 起点URLパス以下を対象
        prefix = parsed_start.path
        if not prefix.endswith('/'):
            prefix += '/'
        self._start_prefix = prefix
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._count_errors = 0

    async def run(self) -> list[LinkResult]:
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = {"User-Agent": self.config.user_agent}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            await self._crawl_url(session, self.config.start_url, 0)
        return self._results

    def _report_progress(self, current: str):
        if self.progress_callback:
            pages = len(self._visited)
            errors = self._count_errors
            self.progress_callback(pages, errors, current)

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if self.config.include_subdomains:
            if not (netloc == self._start_host or netloc.endswith("." + self._start_host)):
                return False
        elif self.config.same_origin:
            if netloc != self._start_host:
                return False
        # サブディレクトリ制限: 起点URLパス以下のみ許可
        if not parsed.path.startswith(self._start_prefix):
            return False
        if self.config.exclude and any(p in url for p in self.config.exclude):
            return False
        if self.config.include and not any(p in url for p in self.config.include):
            return False
        return True

    async def _crawl_url(self, session: aiohttp.ClientSession, url: str, depth: int):
        if self.config.cancel_event.is_set():
            return
        # 最大深度: max_depth < 0 の場合は無制限
        if self.config.max_depth >= 0 and depth > self.config.max_depth:
            return
        if url in self._visited:
            return
        self._visited.add(url)
        await asyncio.sleep(self.config.delay)
        try:
            async with self._semaphore:
                async with session.get(url) as resp:
                    html = await resp.text()
        except Exception:
            return

        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            soup = BeautifulSoup(html, "lxml")

        tag_attrs = [("a", "href")]
        if self.config.check_resources:
            tag_attrs += [("img", "src"), ("link", "href"), ("script", "src")]

        seen = set()
        all_links: list[tuple[str, str]] = []
        for tag, attr in tag_attrs:
            for elem in soup.find_all(tag):
                raw = elem.get(attr)
                if not raw or raw.startswith("#"):
                    continue
                absl = urljoin(url, raw)
                if not self._is_allowed(absl):
                    continue
                if absl in seen:
                    continue
                seen.add(absl)
                all_links.append((absl, tag))

        check_coros = [self._check_link(session, url, link) for link, _ in all_links]
        child_coros = [self._crawl_url(session, link, depth + 1)
                      for link, tag in all_links if tag == "a"]
        if check_coros:
            await asyncio.gather(*check_coros)
        if child_coros:
            await asyncio.gather(*child_coros)

    async def _check_link(self, session: aiohttp.ClientSession,
                          source: str, link: str):
        """
        単一リンクのステータスをチェックし、結果を記録。
        既にチェック済みのリンクはキャッシュ結果を再利用。
        """
        # 中断判定
        if self.config.cancel_event.is_set():
            return
        # リクエスト間隔
        await asyncio.sleep(self.config.delay)
        # キャッシュがあれば再利用
        if link in self._link_cache:
            status, error, is_broken = self._link_cache[link]
            # キャッシュ再利用時もエラー件数には含める
            if is_broken:
                self._count_errors += 1
        else:
            status: Optional[int] = None
            error: Optional[str] = None
            is_broken = False
            try:
                async with self._semaphore:
                    # HEAD リクエストでチェック
                    try:
                        resp = await session.head(link, allow_redirects=True)
                    except Exception:
                        resp = await session.get(link, allow_redirects=True)
                    status = resp.status
                    await resp.release()
                # broken 判定
                if status is not None and (status >= 400 or status in self.config.error_codes):
                    is_broken = True
                    self._count_errors += 1
            except Exception as e:
                error = str(e)
                is_broken = True
                self._count_errors += 1
            # キャッシュ保存
            self._link_cache[link] = (status, error, is_broken)
        # 結果を記録
        result = LinkResult(
            source=source,
            target=link,
            status=status,
            error=error,
            is_broken=is_broken,
        )
        self._results.append(result)
        # 進捗通知
        self._report_progress(link)