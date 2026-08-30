import csv
import datetime
import re
import urllib.parse
from collections.abc import Iterator
from pathlib import Path

import feedgenerator
import requests
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader

YANMAGA_BASE = "https://yanmaga.jp"
COMICS_URL_PREFIX = f"{YANMAGA_BASE}/comics/"
FEED_CSV = Path("feed.csv")
FEEDS_DIR = Path("feeds")
TEMPLATES_DIR = "templates"
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
# feed.csv は "id,title" の 2 列
FEED_CSV_COLUMNS = 2
REQUEST_TIMEOUT_SEC = 30


def iter_feed_rows(csv_path: Path) -> Iterator[tuple[str, str]]:
    with csv_path.open() as f:
        for row in csv.reader(f):
            if len(row) < FEED_CSV_COLUMNS:
                print(f"Skipping invalid row: {row}")
                continue
            feed_id, feed_title = row[0], row[1]
            if not ID_PATTERN.fullmatch(feed_id):
                print(f"Skipping invalid id: {feed_id!r}")
                continue
            yield feed_id, feed_title


def parse_episode_date(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text + " 00:00:00+0900", "%Y/%m/%d %H:%M:%S%z")


def build_feed(session: requests.Session, feed_title: str) -> feedgenerator.Atom1Feed | None:
    comics_url = COMICS_URL_PREFIX + feed_title
    response = session.get(comics_url, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    thumbnail = soup.find("div", class_="detailv2-thumbnail-image")
    if thumbnail is None or thumbnail.img is None:
        return None
    detail_img = thumbnail.img

    feed = feedgenerator.Atom1Feed(
        title=detail_img.get("alt"),
        link=comics_url,
        description="",
        language="ja",
        image=detail_img.get("src"),
    )

    for episode in soup.find_all("div", class_="mod-episode-public"):
        if not isinstance(episode, Tag):
            continue
        if episode.find("span", class_="mod-episode-point--free") is None:
            continue

        # bs4 は要素が見つからなければ None を返す。DOM が変わった場合に実行ごと
        # AttributeError で落とさず、該当エピソードだけ飛ばして残りを配信する。
        link_el = episode.a
        title_el = episode.find("p", class_="mod-episode-title")
        date_el = episode.find("time", class_="mod-episode-date")
        if link_el is None or not isinstance(title_el, Tag) or not isinstance(date_el, Tag):
            print("Skipping episode: expected elements not found")
            continue
        href = link_el.get("href")
        if not isinstance(href, str):
            print("Skipping episode: href not found")
            continue

        feed.add_item(
            unique_id=href.rsplit("/", 1)[1],
            title=title_el.text,
            link=YANMAGA_BASE + href,
            description="",
            pubdate=parse_episode_date(date_el.text),
            content="",
        )

    return feed


def write_feed(feed: feedgenerator.Atom1Feed, feed_id: str) -> None:
    with (FEEDS_DIR / f"{feed_id}.xml").open("w") as fp:
        feed.write(fp, "utf-8")


def render_index(feeds: list[dict[str, str]]) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    return env.get_template("index.html").render(feeds=feeds)


def main() -> None:
    rendered_feeds: list[dict[str, str]] = []
    session = requests.Session()

    for feed_id, feed_title in iter_feed_rows(FEED_CSV):
        feed = build_feed(session, feed_title)
        if feed is None:
            print(f"Skipping {feed_id}: thumbnail not found")
            continue
        write_feed(feed, feed_id)
        rendered_feeds.append({"id": feed_id, "title": urllib.parse.unquote(feed_title)})

    (FEEDS_DIR / "index.html").write_text(render_index(rendered_feeds))


if __name__ == "__main__":
    main()
