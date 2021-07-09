import discord


def bold(text: str, escape_formatting: bool = True) -> str:
    """Get the given text in bold.
    Note: By default, this function will escape ``text`` prior to emboldening.
    Parameters
    ----------
    text : str
        The text to be marked up.
    escape_formatting : `bool`, optional
        Set to :code:`False` to not escape markdown formatting in the text.
    Returns
    -------
    str
        The marked up text.
    """
    text = escape(text, formatting=escape_formatting)
    return "**{}**".format(text)


def box(text: str, lang: str = "") -> str:
    """Get the given text in a code block.
    Parameters
    ----------
    text : str
        The text to be marked up.
    lang : `str`, optional
        The syntax highlighting language for the codeblock.
    Returns
    -------
    str
        The marked up text.
    """
    return "```{}\n{}\n```".format(lang, text)


def escape(text: str, *, mass_mentions: bool = False, formatting: bool = False) -> str:
    """Get text with all mass mentions or markdown escaped.
    Parameters
    ----------
    text : str
        The text to be escaped.
    mass_mentions : `bool`, optional
        Set to :code:`True` to escape mass mentions in the text.
    formatting : `bool`, optional
        Set to :code:`True` to escape any markdown formatting in the text.
    Returns
    -------
    str
        The escaped text.
    """
    if mass_mentions:
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
    if formatting:
        text = discord.utils.escape_markdown(text)
    return text


def hyperlink(text: str, link: str):
    """Turns text into a hyperlink.
    Parameters
    ----------
    text : str
        The text that turns `blue`.
    link : str
        The link
    Returns
    -------
    str
        The hyperlink.
    """
    ret = "[{}]({})".format(text, link)
    return ret
