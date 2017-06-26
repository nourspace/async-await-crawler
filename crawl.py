"""Async/await crawler."""

import argparse
import asyncio
import logging
import sys

from crawler import Crawler

ARGS = argparse.ArgumentParser(description="async/await crawler")
ARGS.add_argument(
    'root', help='Root URL')
ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level', default=2, help='Verbose logging (repeat for more verbose)')
ARGS.add_argument(
    '-o', '--out', dest='out', default='sitemap.html', help='Sitemap output file')


def fix_url(url):
    """Prefix a schema-less URL with http://."""
    if '://' not in url:
        url = 'http://' + url
    return url


def main():
    args = ARGS.parse_args()
    if not args.root:
        print('Use --help for command line help')
        return

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels) - 1)])

    loop = asyncio.get_event_loop()
    root = fix_url(args.root)

    crawler = Crawler(root=root, loop=loop, out=args.out)
    try:
        loop.run_until_complete(crawler.crawl())
    except KeyboardInterrupt:
        sys.stderr.flush()
        print('\nInterrupted\n')
    finally:
        crawler.report()
        crawler.close()

        # next two lines are required for actual aiohttp resource cleanup
        # Todo (Nour): Check!
        loop.stop()
        loop.run_forever()

        loop.close()


if __name__ == '__main__':
    main()
