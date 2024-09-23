#!/usr/bin/env python3
import os
import re
import shutil
from subprocess import run
from os.path import dirname, realpath
from datetime import datetime
from pathlib import Path

import yaml
import toml

from scripts import *

PARENT_DIR = dirname(realpath(__file__))

"""
makefile-style build script but its python

note: imports all environment variables at invocation
"""

### GLOBALS

# import my personal data from a separate yaml
with open(f"{PARENT_DIR}/../info.yml", 'r') as yf:
    info = yaml.load(yf, yaml.Loader)

RE_MD = re.compile(r"\+{3}(?P<front_matter>.+)\+{3}(?P<content>.+)\s+", re.S)


### TARGETS

@default
def build_all():
    publications()
    teaching()
    config()
    index()
    contact()
    tailwind()
    build('--output-dir', 'docs', '--force')


@target
def build(*args):
    run(['zola', 'build', *args])

@target
def tailwind(*args):
    run(['tailwindcss', '-i', 'styles/styles.css', '-o', 'static/styles/styles.css'])

@target
def config():

    config = {
        "title": "Ryan Tsang",
        "base_url": "https://rctsang.github.io",
        "compile_sass": False,
        "build_search_index": False,
        "ignored_content": [
            "*/blog/_wip-*",
        ],
        "translations": {
            "Biography": "Biography",
            "Interests": "Interests",
            "Education": "Education",
            "toc": "Table of Contents",
            "Published": "Published",
            "Abstract": "Abstract",
            "volume": "volume",
            "number": "number",
            "pages": "pages",
        },
        "slugify": {
            "paths": "on",
            "taxonomies": "on",
            "anchors": "on",
        },
        "markdown": {
            "highlight_code": True,
        },
        "extra": {
            "email": info['email'].replace('@', '[at]'),
            "avatar": "img/avatar.jpg",
            "favicon": "img/favicon.ico",
            "contact_in_index": True,
            "menu_items": [
                { "path": "#contacts", "name": "Contact"},
            ],
        }
    }

    with open(f"{PARENT_DIR}/config.toml", 'w') as tf:
        toml.dump(config, tf)

@target
def index():

    front_matter = {
        "title": "Home",
        "page_template": "page.html",
        "extra": {
            "title": "",
            "interests": [
                "Embedded Systems",
                "Firmware Security",
                "STEM Education",
            ],
            "education": {
                "degrees": [
                    {
                        "degree": edu["studyType"],
                        "institution": edu["institution"],
                        "year": edu["endDate"].year,
                    } for edu in info["education"]
                ],
            },
            "avatar_icons": [
                { "icon": profile["type"], "link": profile["url"] } \
                for profile in info["profiles"] if profile['network'] != "Github (Personal)"
            ]
        }
    }

    front_matter = toml.dumps(front_matter)

    with open(f"{PARENT_DIR}/content/_index.md", 'r') as mdf:
        current_data = mdf.read()

    data = RE_MD.sub(f"+++\n{front_matter}\n+++\\g<content>", current_data)
    data = data.rstrip('\n') + '\n'

    with open(f"{PARENT_DIR}/content/_index.md", 'w') as mdf:
        mdf.write(data)

@target
def contact():

    front_matter = {
        "title": "Contact",
        "template": "contact-page.html",
        "path": "contacts",
        "extra": {
            "links": [
                {
                    "icon": profile['type'],
                    "name": profile['network'],
                    "link": profile['url'],
                } for profile in info['profiles']
            ]
        }
    }

    front_matter = toml.dumps(front_matter)

    with open(f"{PARENT_DIR}/content/contacts.md", 'r') as mdf:
        current_data = mdf.read()

    data = RE_MD.sub(f"+++\n{front_matter}\n+++\\g<content>", current_data)
    data = data.rstrip('\n') + '\n'

    with open(f"{PARENT_DIR}/content/contacts.md", 'w') as mdf:
        mdf.write(data)

@target
def publications():

    index_front_matter = {
        "title": "Research",
        "sort_by": "date",
        "template": "publications.html",
        "page_template": "publication-page.html",
        "insert_anchor_links": "right",
        "weight": 2,
        "extra": {
            "index_title": "Publications",
            "index_show": True,
            "hidden_nav": False,
            "publications_types": [
                # { "title": "Thesis", "type": "thesis" },
                { "title": "Conference Papers", "type": "conference" },
                # { "title": "Journal Articles", "type": "journal" },
            ],
        },
    }

    index_front_matter = toml.dumps(index_front_matter)

    path = Path(f"{PARENT_DIR}/content/publications/_index.md")
    assert path.exists(), "{} does not exist!".format(path)

    with open(path, 'r') as mdf:
        current_data = mdf.read()

    data = RE_MD.sub(f"+++\n{index_front_matter}\n+++\\g<content>", current_data)
    data = data.rstrip('\n') + '\n'

    with open(path, 'w') as mdf:
        mdf.write(data)

    for pub in info['publications']:
        front_matter = {
            "title": pub['name'],
            "date": pub['releaseDate'],
            "extra": {
                "authors": pub['authors'],
                "publications_types": pub['pubType'],
                "featured": pub['featured'],
                "type": pub['type'],
                "publication": pub['publication'],
                "pdf": pub['file'],
            }
        }

        front_matter = toml.dumps(front_matter)

        path = Path(f"{PARENT_DIR}/content/publications/{pub['id']}")
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "index.md", 'w') as mdf:
            mdf.write(f"+++\n{front_matter}\n+++\n")

        shutil.copy(f"{PARENT_DIR}/../publications/{pub['bibtex']}", str(path / pub['bibtex']))
        shutil.copy(f"{PARENT_DIR}/../publications/{pub['file']}", str(path / pub['file']))


@target
def teaching():

    for institution in info['teaching']:
        institution['start'] = institution['startDate'].strftime('%b %Y')
        institution['end'] = institution['endDate'].strftime('%b %Y')

    front_matter = {
        "title": "Teaching",
        "template": "teaching.html",
        "extra": {
            "institutions": [ institution for institution in info['teaching'] ],
        }
    }

    front_matter = toml.dumps(front_matter)

    path = Path(f"{PARENT_DIR}/content/teaching/_index.md")
    assert path.exists(), "{} does not exist!".format(path)

    with open(path, 'r') as mdf:
        current_data = mdf.read()

    data = RE_MD.sub(f"+++\n{front_matter}\n+++\\g<content>", current_data)
    data = data.rstrip('\n') + '\n'

    with open(path, 'w') as mdf:
        mdf.write(data)




