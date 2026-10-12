"""Publication settings for the native Zig 0.17.0 edition."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "sphinx-plugins"))

project = "Lord of the io_uring — Zig 0.17.0"
author = "Shuveb Hussain; Zig adaptation by Ahmed Alhulaibi"
copyright = "2020, Shuveb Hussain; Zig adaptation, Ahmed Alhulaibi"
version = release = "0.17.0"
root_doc = "index"
extensions = ["manpage", "zig_lexer"]
man_url_regex = "https://man.archlinux.org/man/${topic}.${num}.en"
exclude_patterns = [
    "_build/**", ".venv/**", ".zig-cache/**", "zig-out/**", ".git/**",
    "conversion/**", "examples/**", "tests/**", "tools/**", "Thumbs.db", ".DS_Store",
]
language = "en"
highlight_language = "zig"
html_theme = "alabaster"
html_logo = "_static/io_uring_logo.png"
html_static_path = ["_static"]
html_theme_options = {"show_relbars": True}
html_title = project
html_use_index = False
html_css_files = ["ebook.css"]

# Retain the upstream licence in both rendered editions.
html_extra_path = ["LICENSE"]
epub_basename = "Lord-of-the-io_uring-Zig-0.17.0"
epub_title = project
epub_author = author
epub_language = "en"
epub_publisher = "ahmedalhulaibi/loti-zig"
epub_copyright = copyright
epub_identifier = "loti-zig-0.17.0"
epub_scheme = "publisher-id"
epub_uid = "loti-zig-0.17.0"
epub_description = "Native Zig 0.17.0 adaptation of Shuveb Hussain's Linux asynchronous I/O guide."
epub_show_urls = "no"
epub_tocdepth = 3
epub_use_index = False
epub_exclude_files = ["search.xhtml", "genindex.xhtml", "LICENSE", ".buildinfo.bak"]
