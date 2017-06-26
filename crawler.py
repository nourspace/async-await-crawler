import logging
import urllib.parse

from collections import namedtuple
import asyncio
import aiohttp
import re

LOGGER = logging.getLogger(__name__)


def url_host(url):
    return urllib.parse.urlparse(url).netloc


Link = namedtuple('Link', ['url', 'urls'])


class MaxPagesReached(Exception):
    pass


class Crawler:
    def __init__(self, root, loop, out=None):
        self.root = root
        self.loop = loop
        self.q = asyncio.Queue(loop=self.loop)
        self.client = aiohttp.ClientSession(loop=self.loop)
        self.seen_urls = set()
        self.done = []
        self.root_host = url_host(self.root)
        self.add_url(root)
        self.time_out = 10
        self.max_pages = 1000
        self.out = out or 'sitemap.html'

    def close(self):
        """Closes resources."""
        self.client.close()

    async def crawl(self):
        """
        Starts crawling until there are no more pages (getting an item from queue times out) or max pages is reached.
        """
        while True:
            try:
                url = await asyncio.wait_for(self.q.get(), self.time_out)
                await self.fetch(url)
                self.q.task_done()
                if self.max_pages and len(self.done) > self.max_pages:
                    raise MaxPagesReached
            except asyncio.TimeoutError:
                LOGGER.info('no more pages to crawl')
                break
            except MaxPagesReached:
                LOGGER.info('reached max pages')
                break

    async def parse(self, response):
        """Returns a list of urls."""
        urls = set()
        await response.read()

        if response.status == 200:
            if 'text/html' in response.headers.get('content-type', ''):
                text = await response.text()
                hrefs = set(re.findall(r'''(?i)href=["']([^\s"'<>]+)''', text))
                if hrefs:
                    LOGGER.info('got %d urls from %s', len(hrefs), response.url)
                for href in hrefs:
                    normalized = urllib.parse.urljoin(str(response.url), href)
                    defrag, frag = urllib.parse.urldefrag(normalized)
                    if self.url_allowed(defrag):
                        urls.add(defrag)

        return urls

    async def fetch(self, url):
        """Fetches one URL."""
        try:
            response = await self.client.get(url)
        except aiohttp.ClientError as client_error:
            LOGGER.info('fetch %s raised %r', url, client_error)
            self.done_link(Link(url=url, urls=[]))
            return

        try:
            urls = await self.parse(response)
            link = Link(url=url, urls=urls)
            self.done_link(link)
            for sub_url in link.urls.difference(self.seen_urls):
                self.add_url(sub_url)
        finally:
            await response.release()

    def url_allowed(self, url):
        """Returns whether a url is allowed"""
        parts = urllib.parse.urlparse(url)
        if parts.scheme not in ('http', 'https'):
            LOGGER.debug('skipping non-http scheme in %s', url)
            return False
        if url_host(url) != self.root_host:
            LOGGER.debug('skipping non-root host in %s', url)
            return False
        return True

    def add_url(self, url):
        """Adds a URL to the queue if not seen before."""
        LOGGER.debug('adding %s', url)
        if url not in self.seen_urls:
            self.seen_urls.add(url)
            self.q.put_nowait(url)

    def done_link(self, link):
        """Adds a link to done list."""
        LOGGER.debug('added %s', link.url)
        self.done.append(link)

    def report(self):
        """Exports a sitemap.html with all the links and their children."""
        html = """<html>
    <body>
        <ul>
            {}
        </ul>
    </body>
</html>
        """
        ul = ''
        for link in self.done:
            ul += self._link_html(link)

        with open(self.out, 'w') as f:
            f.write(html.format(ul))
            LOGGER.info('exported sitemap to s', self.out)

    def _link_html(self, link):
        html = '<li>'
        html += '<a href="{0}">{0}</a>'.format(link.url)
        if link.urls:
            html += '<ul>'
            for url in link.urls:
                html += '<li><a href="{0}">{0}</a></li>'.format(url)
            html += '</ul>'
        html += '</li>'
        return html
