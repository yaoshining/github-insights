#!/usr/bin/env python3
"""Validate generated navigation and one daily report, without rewriting history."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from update_indexes import ROOT, scan_reports

class Document(HTMLParser):
    void = set('area base br col embed hr img input link meta param source track wbr'.split())
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack, self.links, self.ids = [], [], set()
        self.feed(text)
        assert not self.stack, f'Unclosed tags: {self.stack}'
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in self.void:
            self.stack.append(tag)
        if 'href' in attrs:
            self.links.append(attrs['href'])
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, f'Duplicate id: {attrs["id"]}'
            self.ids.add(attrs['id'])
    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f'Misnested closing tag: {tag}'
        self.stack.pop()

def validate(day):
    reports = scan_reports()
    assert day in reports, f'Missing daily report: {day}'
    years = {d[:4] for d in reports}
    months = {d[:4]+'/'+d[5:7] for d in reports}
    pages = {ROOT/'index.html', reports[day][0]}
    pages.update(ROOT/'reports'/y/'index.html' for y in years)
    pages.update(ROOT/'reports'/m/'index.html' for m in months)
    targets = set()
    for path in pages:
        text = path.read_text()
        assert text.lower().startswith('<!doctype html>'), path
        assert '<html lang="zh-CN">' in text and 'charset="UTF-8"' in text and 'name="viewport"' in text, path
        doc = Document(text)
        for href in doc.links:
            u = urlsplit(href)
            if u.scheme or u.netloc:
                continue
            target = (path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
            assert target.is_relative_to(ROOT), f'Link escapes site: {path}: {href}'
            if target.is_dir():
                target /= 'index.html'
            assert target.is_file(), f'Broken link: {path}: {href}'
            if not u.path and u.fragment:
                assert u.fragment in doc.ids, f'Missing anchor {href}'
            targets.add(target)
    for aliases in reports.values():
        for report in aliases:
            assert report.resolve() in targets, f'Report omitted from navigation: {report}'
    home = (ROOT/'index.html').read_text()
    latest = next(iter(reports))
    assert f'datetime="{latest}"' in home
    assert reports[latest][0].relative_to(ROOT).as_posix() in home
    print(f'PASS: {len(pages)} pages, {len(reports)} dates, {sum(map(len,reports.values()))} historical URLs; HTML structure and internal links valid')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('date',help='Daily report date, YYYY-MM-DD')
    validate(parser.parse_args().date)
