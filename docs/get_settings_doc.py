"""Retrieve docstring from midani_settings.py and convert to settings.md
"""

import re
import os

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))
OUT_PATH = os.path.join(SCRIPT_PATH, "settings.md")


def to_markdown():
    with open(
        os.path.join(SCRIPT_PATH, "../src/midani_settings.py"), "r"
    ) as inf:
        docstring = re.search(
            r'Settings:\s+"""(.*?)"""', inf.read(), re.MULTILINE + re.DOTALL
        )[1]

    kwarg_pattern = re.compile(r"^ {8}(\w+(, \w+)*):", flags=re.MULTILINE)
    docstring = re.sub(kwarg_pattern, r"- **\1**:", docstring)
    subkwarg_pattern = re.compile(r"^ {16}(\"\w+\")", flags=re.MULTILINE)
    docstring = re.sub(subkwarg_pattern, r"    - \1", docstring)

    subheading_pattern = re.compile(
        r"^$\n {8}([^\n]+)\n {8}=+\n^$", flags=re.MULTILINE
    )
    docstring = re.sub(subheading_pattern, r"\n## \1 \n", docstring)
    default_pattern = re.compile(r"^( +)Default: (.*)", flags=re.MULTILINE)
    docstring = re.sub(default_pattern, r"\1*Default*: `\2`", docstring)
    paragraph_pattern = re.compile(r"^$\n {4,8}([^\n]+)\n", flags=re.MULTILINE)
    docstring = re.sub(paragraph_pattern, r"\n\1\n", docstring)
    return docstring


PREAMBLE = "# Midani settings\n\n"


def main():
    docstring = to_markdown()
    docstring = docstring.split("\n\n", maxsplit=3)[3]
    docstring = docstring.replace("Keyword args:", "")
    with open(OUT_PATH, "w") as outf:
        outf.write(PREAMBLE)
        outf.write(docstring)


if __name__ == "__main__":
    main()
