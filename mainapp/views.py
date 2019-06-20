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
    fix_svgs(soup_html)
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
    download_missing_files_to_static(font_urls)
    update_html_font_paths(soup_html, font_urls)


def collect_font_urls_from_html(soup_html):
    font_urls = []
    for style_tag in soup_html.find_all('style'):
        font_urls.extend(re.findall(r"url\((.*?)\)", style_tag.text))
    return set([f.split('?')[0] for f in font_urls])


def update_html_font_paths(soup_html, font_urls):
    for style_tag in soup_html.find_all('style'):
        style_tag_text = style_tag.text
        for font_url in font_urls:
            style_tag_text = style_tag_text.replace('(' + font_url, '(/static/mainapp' + font_url)
        style_tag.string = style_tag_text


def fix_svgs(soup_html):
    svg_urls = collect_svg_urls_from_html(soup_html)
    download_missing_files_to_static(svg_urls)
    update_html_svg_paths(soup_html)


def collect_svg_urls_from_html(soup_html):
    svg_urls = set()
    for svg_tag in soup_html.find_all('svg'):
        use = svg_tag.use
        if use:
            svg_urls.add(use.get('xlink:href').split('#')[0])
    return svg_urls


def update_html_svg_paths(soup_html):
    for svg_tag in soup_html.find_all('svg'):
        use_tag = svg_tag.use
        if use_tag:
            use_tag['xlink:href'] = use_tag['xlink:href'].replace(HABR, '/static/mainapp')


def download_missing_files_to_static(urls_list):
    for file_url in urls_list:
        file_path = os.path.join(BASE_DIR, 'static', 'mainapp', *file_url.replace(HABR, '').split('/'))
        if not os.path.exists(file_path):
            file_extension = file_path.split('.')[-1]
            print("Downloading missing {} file to {}".format(file_extension, file_path))
            # fonts come without https://habr.com, while svg comes with it, so both cases are handled in the next line
            abs_file_url = file_url if HABR in file_url else HABR + file_url
            r = requests.get(abs_file_url)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as file_obj:
                file_obj.write(r.content)
