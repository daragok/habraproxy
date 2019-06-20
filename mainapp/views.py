import os
import re

import bs4
import requests
from django.http import HttpResponse

from habr_parser.settings import BASE_DIR

TRADE_MARK_SIGN = "\u2122"
WORD_PATTERN = r"[^\W\d_]{6}"
WORD_PATTERN_WITH_BOUNDARIES = r"\b{}\b".format(WORD_PATTERN)
HABR = 'https://habr.com'


def main_view(request):
    habr_url = HABR + request.path
    r = requests.get(habr_url)
    soup_html = bs4.BeautifulSoup(r.text, features="html5lib")
    add_trademarks_to_all_words_of_length_six(soup_html)
    my_port = request.META['SERVER_PORT']
    update_habr_urls_to_my_server_urls(soup_html, my_port)
    fix_fonts(soup_html)
    return HttpResponse(soup_html.encode('utf-8'))


def add_trademarks_to_all_words_of_length_six(soup_html):
    for text_piece in soup_html.find_all(text=re.compile(WORD_PATTERN_WITH_BOUNDARIES, re.UNICODE)):
        if text_piece.parent.name in ['script', 'style']:
            # skip javascript tags and CSS
            continue
        if isinstance(text_piece, bs4.element.Comment):
            # skip html comments
            continue
        update_text_piece(text_piece)
    return soup_html


def update_text_piece(text_piece):
    words_to_replace = get_words_to_replace(text_piece)
    updated_text_piece = text_piece
    for word in words_to_replace:
        new_word = word + TRADE_MARK_SIGN
        updated_text_piece = re.sub(r"\b{}\b".format(word), new_word, updated_text_piece)
    text_piece.replace_with(updated_text_piece)


def get_words_to_replace(text):
    return set(re.findall(WORD_PATTERN_WITH_BOUNDARIES, text, re.UNICODE))


def update_habr_urls_to_my_server_urls(soup_html, port):
    for a in soup_html.find_all('a'):
        if a.get('href') and HABR in a['href']:
            a['href'] = a['href'].replace(HABR, 'http://127.0.0.1:{}'.format(port))


def fix_fonts(soup_html):
    font_urls = collect_font_urls_from_html(soup_html)
    download_missing_fonts_to_static(font_urls)
    update_html_font_paths(soup_html, font_urls)


def collect_font_urls_from_html(soup_html):
    font_urls = []
    for style_tag in soup_html.find_all('style'):
        font_urls.extend(re.findall(r"url\((.*?)\)", style_tag.text))
    return set([f.split('?')[0] for f in font_urls])


def download_missing_fonts_to_static(font_urls):
    for font_url in font_urls:
        font_file_path = os.path.join(BASE_DIR, 'static', 'mainapp', *font_url.split('/'))
        if not os.path.exists(font_file_path):
            print("Downloading missing font to {}".format(font_file_path))
            abs_font_url = HABR + font_url
            r = requests.get(abs_font_url)
            os.makedirs(os.path.dirname(font_file_path), exist_ok=True)
            with open(font_file_path, 'wb') as font_file:
                font_file.write(r.content)


def update_html_font_paths(soup_html, font_urls):
    for style_tag in soup_html.find_all('style'):
        style_tag_text = style_tag.text
        for font_url in font_urls:
            style_tag_text = style_tag_text.replace('(' + font_url, '(/static/mainapp' + font_url)
        style_tag.string = style_tag_text
