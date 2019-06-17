import re

import bs4
import requests
from django.http import HttpResponse

TRADE_MARK_SIGN = "\u2122"
WORD_PATTERN = r"[^\W\d_]{6}"
WORD_PATTERN_WITH_BOUNDARIES = r"\b{}\b".format(WORD_PATTERN)
HABR = 'https://habr.com'


def main_view(request):
    habr_url = HABR + request.path
    r = requests.get(habr_url)
    soup_html = bs4.BeautifulSoup(r.text, features="html.parser")
    add_trademarks_to_all_words_of_length_six(soup_html)
    my_port = request.META['SERVER_PORT']
    update_habr_urls_to_my_server_urls(soup_html, my_port)
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
