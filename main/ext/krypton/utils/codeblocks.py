import collections

__all__ = ('Codeblock', 'CodeConvert')

Codeblock = collections.namedtuple('Codeblock', ['language', 'content'])

def CodeConvert(argument) -> Codeblock:
    """
    A converter that strips codeblock markdown if it exists.
    Returns a namedtuple of (language, content).
    :attr:`Codeblock.language` is an empty string if no language was given with this codeblock.
    It is ``None`` if the input was not a complete codeblock.
    """

    if not argument.startswith('`'):
        return Codeblock(None, argument)
    
    last = collections.deque(maxlen=3)
    backticks = 0
    in_language = False
    in_code = False
    language = []
    code = []

    for char in argument:
        if char == '`' and not in_code and not in_language:
            backticks += 1
        
        if last and last[-1] == '`' and char != '`' or in_code and ''.join(last):
            in_code = True
            code.append(char)
        
        if char == '\n':
            in_language = False
            in_code = True

        elif ''.join(last) == '`' * 3 and char != '`':
            in_language = True
            language.append(char)
        elif in_language:
            if char != '\n':
                language.append(char)

        last.append(char)

    if not code and not language:
        code[:] = last

    return Codeblock(''.join(language), ''.join(code[len(language):-backticks]))