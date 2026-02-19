import csv
import datetime
import re
import urllib.parse
from pathlib import Path

import feedgenerator
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

rendered_feeds = []

with open('feed.csv') as feed_file:
    for feed in csv.reader(feed_file):
        if len(feed) < 2:
            print(f"Skipping invalid row: {feed}")
            continue

        feed_id, feed_title = feed[0], feed[1]

        if not re.fullmatch(r'[A-Za-z0-9_-]+', feed_id):
            print(f"Skipping invalid id: {feed_id!r}")
            continue

        rendered_feeds.append({'id': feed_id, 'title': urllib.parse.unquote(feed_title)})

        comics_url = "https://yanmaga.jp/comics/" + feed_title
        response = requests.get(comics_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        thumbnail = soup.find('div', class_="detailv2-thumbnail-image")
        if thumbnail is None or thumbnail.img is None:
            print(f"Skipping {feed_id}: thumbnail not found")
            continue
        detail_img = thumbnail.img

        rss = feedgenerator.Atom1Feed(
            title=detail_img.get('alt'),
            link=comics_url,
            description='',
            language="ja",
            image=detail_img.get('src')
        )

        for episode in soup.find_all('div', class_="mod-episode-public"):
            if episode.find('span', class_="mod-episode-point--free") is None:
                continue

            href = episode.a.get('href')

            rss.add_item(
                unique_id=href.rsplit('/', 1)[1],
                title=episode.find('p', class_="mod-episode-title").text,
                link="https://yanmaga.jp" + href,
                description="",
                pubdate=datetime.datetime.strptime(episode.find('time', class_="mod-episode-date").text + ' 00:00:00+0900', '%Y/%m/%d %H:%M:%S%z'),
                content=""
            )

        with open(Path('feeds') / (feed_id + '.xml'), 'w') as fp:
            rss.write(fp, 'utf-8')

jinja_env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
jinja_template = jinja_env.get_template('index.html')

with open(Path('feeds') / 'index.html', 'w') as index:
    index.write(jinja_template.render(feeds=rendered_feeds))
