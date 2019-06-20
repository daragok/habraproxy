import os
import unittest

import bs4

from mainapp.views import collect_font_urls_from_html, update_html_font_paths, collect_svg_urls_from_html, \
    update_html_svg_paths


class TestHabraProxyMethods(unittest.TestCase):
    mocks = 'mocks'

    def test_collect_font_urls_from_html(self):
        soup = self._get_mock_html_soup('test_collect_font_urls_from_html.html')
        font_urls = collect_font_urls_from_html(soup)
        self.assertEqual(font_urls, {"/fonts/0/FiraSans/firaSans-medium.ttf",
                                     "/fonts/0/FiraSans/firaSans-medium.woff",
                                     "/fonts/0/FiraSans/firaSans-medium.woff2",
                                     "/fonts/0/FiraSans/firaSans-medium.eot"}
                         )

    def test_update_html_font_paths(self):
        font_urls = {"/fonts/0/FiraSans/firaSans-medium.ttf",
                     "/fonts/0/FiraSans/firaSans-medium.woff",
                     "/fonts/0/FiraSans/firaSans-medium.woff2",
                     "/fonts/0/FiraSans/firaSans-medium.eot"}
        soup = self._get_mock_html_soup('test_update_html_font_paths.html')
        update_html_font_paths(soup, font_urls)
        updated_font_urls = collect_font_urls_from_html(soup)
        self.assertEqual(updated_font_urls, {'/static/mainapp/fonts/0/FiraSans/firaSans-medium.eot',
                                             '/static/mainapp/fonts/0/FiraSans/firaSans-medium.ttf',
                                             '/static/mainapp/fonts/0/FiraSans/firaSans-medium.woff',
                                             '/static/mainapp/fonts/0/FiraSans/firaSans-medium.woff2'}
                         )

    def test_collect_svg_urls_from_html(self):
        soup = self._get_mock_html_soup('test_collect_svg_urls_from_html.html')
        svg_urls = collect_svg_urls_from_html(soup)
        self.assertEqual(svg_urls, {'https://habr.com/images/1560786911/common-svg-sprite.svg'})

    def test_update_html_svg_paths(self):
        soup = self._get_mock_html_soup('test_update_html_svg_paths.html')
        update_html_svg_paths(soup)
        updated_svg_urls = collect_svg_urls_from_html(soup)
        self.assertEqual(updated_svg_urls, {'/static/mainapp/images/1560786911/common-svg-sprite.svg'})

    def _get_mock_html_soup(self, name):
        html_path = os.path.join(self.mocks, name)
        with open(html_path, 'r') as html_file:
            return bs4.BeautifulSoup(html_file, features='html5lib')
