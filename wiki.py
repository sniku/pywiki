

"""Mediawiki terminal client.
Usage:
  wiki_client
  wiki_client [go] <article_name>
  wiki_client [go] <article_name> < stdin_file.txt
  wiki_client append <article_name> <text>
  wiki_client log <article_name> <text>
  wiki_client cat <article_name>
  wiki_client mv <article_name> <new_name> [--leave_redirect]
  wiki_client upload <filepath> [<alt_filename>]
  wiki_client --help
"""

VERSION = "0.1"

import sys
import pywiki.wiki_client
from docopt import docopt

if __name__ == "__main__":
    args = docopt(__doc__, version='Mediawiki client ' + VERSION)
    pywiki.wiki_client.run(args)
