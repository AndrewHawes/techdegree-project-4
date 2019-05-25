import textwrap
import shutil


def get_width():
    return min(shutil.get_terminal_size((80, 20)).columns - 10, 120)


def wraptext(txt):
    split_text = txt.split('\n')
    lines = []
    for line in split_text:
        new = textwrap.wrap(line, width=get_width(), replace_whitespace=False)
        lines.append(new)
    text = []
    for line in lines:
        text.append('\n'.join(line))
    return '\n'.join(text)


def printw(txt):
    print(wraptext(txt))


def inputw(txt):
    return input(wraptext(txt))