
import textwrap

def wrap_text(text, width=200):
    """
    Wrap the given text to the specified width.

    :param text: Text to wrap
    :param width: Width at which to wrap the text
    :return: Wrapped text
    """
    return textwrap.fill(text, width)

