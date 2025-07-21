import datetime
import urllib

from bs4 import BeautifulSoup
import requests
import feedgenerator
import csv

feed_file = open('feed.csv')
feeds = csv.reader(feed_file)

index = open('feeds/index.html', 'w')
index.write('<!DOCTYPE html><html><body><ul>')

for feed in feeds:
    print(feed)
    comics_url = "https://yanmaga.jp/comics/" + feed[1]
    comics = requests.get(comics_url).text

    soup = BeautifulSoup(comics, 'html.parser')

    detail_img = soup.find('div', class_="detailv2-thumbnail-image").img
    print(detail_img.get('alt'))

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

    with open('feeds/' + feed[0] + '.xml', 'w') as fp:
        rss.write(fp, 'utf-8')

    index.write('<li><a href="{href}">{title}</a></li>'.format(href=feed[0] + '.xml', title=urllib.parse.unquote(feed[1])))

index.write('</ul></body></html>')
