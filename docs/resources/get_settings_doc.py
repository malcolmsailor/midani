"""Retrieve docstring from midani_settings.py and convert to settings.md
"""

import re
import os

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))
OUT_PATH = os.path.join(SCRIPT_PATH, "../settings.md")
PREAMBLE = """# Midani settings

"""


def get_code_block_replacement(code_block):
    indent_len = len(
        re.search(r"(?P<indent> *)```$", code_block).group("indent")
    )
    indent_pattern = re.compile(r"^" + " " * indent_len, re.MULTILINE)
    return re.sub(indent_pattern, "", code_block)


def get_docstring():
    with open(
        os.path.join(SCRIPT_PATH, "../../src/midani_settings.py"), "r"
    ) as inf:
        docstring = re.search(
            r'^class Settings:\s+"""(.*?)"""',
            inf.read(),
            re.MULTILINE + re.DOTALL,
        )[1]

    kwarg_pattern = re.compile(r"^ {8}(\w+(, \w+)*):", flags=re.MULTILINE)
    docstring = re.sub(kwarg_pattern, r"- **\1**:", docstring)
    # As a hack to avoid subkwarg_pattern picking up dictionary keys in
    # code-blocks, I add an extra space before the colon in these items
    # in the docstring
    subkwarg_pattern = re.compile(r"^ {16}(\"\w+\") :", flags=re.MULTILINE)
    docstring = re.sub(subkwarg_pattern, r"    - \1:", docstring)

    subheading_pattern = re.compile(
        r"^$\n {8}([^\n]+)\n {8}=+\n^$", flags=re.MULTILINE
    )
    docstring = re.sub(subheading_pattern, r"\n### \1 \n", docstring)
    default_pattern = re.compile(r"^( +)Default: (.*)", flags=re.MULTILINE)
    docstring = re.sub(default_pattern, r"\1*Default*: `\2`", docstring)
    paragraph_pattern = re.compile(r"^$\n {4,8}([^\n]+)\n", flags=re.MULTILINE)
    docstring = re.sub(paragraph_pattern, r"\n\1\n", docstring)
    docstring = docstring.split("\n\n", maxsplit=3)[3]
    docstring = docstring.replace("Keyword args:", "")
    # Process code blocks:
    code_block_pattern = re.compile(
        r"^ *```.*?^ *```", re.MULTILINE + re.DOTALL
    )
    code_blocks = re.findall(code_block_pattern, docstring)
    for block in code_blocks:
        docstring = docstring.replace(block, get_code_block_replacement(block))
    return docstring


def get_readme():
    with open(os.path.join(SCRIPT_PATH, "../../README.md"), "r") as inf:
        readme = re.search(
            r"## Configuration\n(.*?)##", inf.read(), re.MULTILINE + re.DOTALL
        )[1]
    readme = re.sub(
        r"^.*settings\.md.*$",
        r"See also the general documentation in README.md\n\n## General usage",
        readme,
        flags=re.MULTILINE,
    )
    readme = re.sub(
        r"^(.*example.*)$",
        r"## Example\n\n\1",
        readme,
        count=1,
        flags=re.MULTILINE,
    )

    return readme


def main():
    readme = get_readme()
    docstring = get_docstring()

    with open(OUT_PATH, "w") as outf:
        outf.write(PREAMBLE)
        outf.write(readme)
        outf.write("## Detailed settings\n\n")
        outf.write(docstring)


if __name__ == "__main__":
    main()
