"""Highlight Zig 0.17.0 builtin names and quoted identifiers without lexer errors."""

from pygments.lexer import inherit
from pygments.lexers import ZigLexer
from pygments.token import Name
from sphinx.highlighting import lexers


class Zig017Lexer(ZigLexer):
    tokens = {
        "root": [
            (r'@"(?:\\.|[^"\\])*"', Name),
            (r"@[A-Za-z_][A-Za-z_0-9]*", Name.Builtin),
            inherit,
        ],
    }


def setup(app):
    lexers["zig"] = Zig017Lexer()
    return {"parallel_read_safe": True, "parallel_write_safe": True}
