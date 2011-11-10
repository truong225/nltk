# Natural Language Toolkit: Tokenizers
#
# Copyright (C) 2001-2011 NLTK Project
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
#         Steven Bird <sb@csse.unimelb.edu.au>
#         Trevor Cohn <tacohn@csse.unimelb.edu.au>
# URL: <http://nltk.sourceforge.net>
# For license information, see LICENSE.TXT

r"""
Regular-Expression Tokenizers

A ``RegexpTokenizer`` splits a string into substrings using a regular expression.
For example, the following tokenizer forms tokens out of alphabetic sequences,
money expressions, and any other non-whitespace sequences:

    >>> s = "Good muffins cost $3.88\nin New York.  Please buy me\ntwo of them.\n\nThanks."
    >>> tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')
    >>> tokenizer.tokenize(s)
    ['Good', 'muffins', 'cost', '$3.88', 'in', 'New', 'York', '.',
    'Please', 'buy', 'me', 'two', 'of', 'them', '.', 'Thanks', '.']

A ``RegexpTokenizer`` can use its regexp to match delimiters instead:

    >>> tokenizer = RegexpTokenizer('\s+', gaps=True)
    >>> tokenizer.tokenize(s)
    ['Good', 'muffins', 'cost', '$3.88', 'in', 'New', 'York.',
    'Please', 'buy', 'me', 'two', 'of', 'them.', 'Thanks.']

Note that empty tokens are not returned when the delimiter appears at
the start or end of the string.

The material between the tokens is discarded.  For example,
the following tokenizer selects just the capitalized words:

    >>> capword_tokenizer = RegexpTokenizer('[A-Z]\w+')
    >>> capword_tokenizer.tokenize(s)
    ['Good', 'New', 'York', 'Please', 'Thanks']

This module contains several subclasses of ``RegexpTokenizer``
that use pre-defined regular expressions.

    >>> # Uses '\s*\n\s*\n\s*':
    >>> BlanklineTokenizer().tokenize(s)
    ['Good muffins cost $3.88\nin New York.  Please buy me\ntwo of them.',
    'Thanks.']

All of the regular expression tokenizers are also available as functions:

    >>> regexp_tokenize(s, pattern='\w+|\$[\d\.]+|\S+')
    ['Good', 'muffins', 'cost', '$3.88', 'in', 'New', 'York', '.',
    'Please', 'buy', 'me', 'two', 'of', 'them', '.', 'Thanks', '.']
    >>> wordpunct_tokenize(s)
    ['Good', 'muffins', 'cost', '$', '3', '.', '88', 'in', 'New', 'York',
     '.', 'Please', 'buy', 'me', 'two', 'of', 'them', '.', 'Thanks', '.']
    >>> blankline_tokenize(s)
    ['Good muffins cost $3.88\nin New York.  Please buy me\ntwo of them.', 'Thanks.']

Caution: The function ``regexp_tokenize()`` takes the text as its
first argument, and the regular expression pattern as its second
argument.  This differs from the conventions used by Python's
``re`` functions, where the pattern is always the first argument.
(This is for consistency with the other NLTK tokenizers.)
"""

import re
import sre_constants

from nltk.internals import convert_regexp_to_nongrouping
from nltk.tokenize.api import TokenizerI
from nltk.tokenize.util import regexp_span_tokenize

class RegexpTokenizer(TokenizerI):
    """
    A tokenizer that splits a string using a regular expression, which
    matches either the tokens or the separators between tokens.

        >>> tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')

    :type pattern: str
    :param pattern: The pattern used to build this tokenizer.
        (This pattern may safely contain grouping parentheses.)
    :type gaps: bool
    :param gaps: True if this tokenizer's pattern should be used
        to find separators between tokens; False if this
        tokenizer's pattern should be used to find the tokens
        themselves.
    :type discard_empty: bool
    :param discard_empty: True if any empty tokens `''`
        generated by the tokenizer should be discarded.  Empty
        tokens can only be generated if `_gaps == True`.
    :type flags: int
    :param flags: The regexp flags used to compile this
        tokenizer's pattern.  By default, the following flags are
        used: `re.UNICODE | re.MULTILINE | re.DOTALL`.

    """
    def __init__(self, pattern, gaps=False, discard_empty=True,
                 flags=re.UNICODE | re.MULTILINE | re.DOTALL):
        # If they gave us a regexp object, extract the pattern.
        pattern = getattr(pattern, 'pattern', pattern)
        
        self._pattern = pattern
        self._gaps = gaps
        self._discard_empty = discard_empty
        self._flags = flags
        self._regexp = None
        
        # Remove grouping parentheses -- if the regexp contains any
        # grouping parentheses, then the behavior of re.findall and
        # re.split will change.
        nongrouping_pattern = convert_regexp_to_nongrouping(pattern)

        try: 
            self._regexp = re.compile(nongrouping_pattern, flags)
        except re.error, e:
            raise ValueError('Error in regular expression %r: %s' %
                             (pattern, e))

    def tokenize(self, text):
        # If our regexp matches gaps, use re.split:
        if self._gaps:
            if self._discard_empty:
                return [tok for tok in self._regexp.split(text) if tok]
            else:
                return self._regexp.split(text)

        # If our regexp matches tokens, use re.findall:
        else:
            return self._regexp.findall(text)

    def span_tokenize(self, text):
        if self._gaps:
            for left, right in regexp_span_tokenize(text, self._regexp):
                if not (self._discard_empty and left == right):
                    yield left, right
        else:
            for m in finditer(self._regexp, text):
                yield m.span()
    
    def __repr__(self):
        return ('%s(pattern=%r, gaps=%r, discard_empty=%r, flags=%r)' %
                (self.__class__.__name__, self._pattern, self._gaps,
                 self._discard_empty, self._flags))

class WhitespaceTokenizer(RegexpTokenizer):
    r"""
    Tokenize a string on whitespace (space, tab, newline).
    In general, users should use the string ``split()`` method instead.

        >>> s = "Good muffins cost $3.88\nin New York.  Please buy me\ntwo of them.\n\nThanks."
        >>> WhitespaceTokenizer().tokenize(s)
        ['Good', 'muffins', 'cost', '$3.88', 'in', 'New', 'York.',
        'Please', 'buy', 'me', 'two', 'of', 'them.', 'Thanks.']
    """

    def __init__(self):
        RegexpTokenizer.__init__(self, r'\s+', gaps=True)

class BlanklineTokenizer(RegexpTokenizer):
    """
    Tokenize a string, treating any sequence of blank lines as a delimiter.
    Blank lines are defined as lines containing no characters, except for
    space or tab characters.
    """
    def __init__(self):
        RegexpTokenizer.__init__(self, r'\s*\n\s*\n\s*', gaps=True)

class WordPunctTokenizer(RegexpTokenizer):
    """
    Tokenize a text into a sequence of alphabetic and
    non-alphabetic characters, using the regexp ``\w+|[^\w\s]+``. 

        >>> s = "Good muffins cost $3.88\\nin New York.  Please buy me\\ntwo of them.\\n\\nThanks."
        >>> WordPunctTokenizer().tokenize(s)
        ['Good', 'muffins', 'cost', '$', '3', '.', '88', 'in', 'New', 'York',
        '.', 'Please', 'buy', 'me', 'two', 'of', 'them', '.', 'Thanks', '.']
    """
    def __init__(self):
        RegexpTokenizer.__init__(self, r'\w+|[^\w\s]+')

######################################################################
#{ Tokenization Functions
######################################################################

def regexp_tokenize(text, pattern, gaps=False, discard_empty=True,
                    flags=re.UNICODE | re.MULTILINE | re.DOTALL):
    """
    Return a tokenized copy of *text*.  See :class:`.RegexpTokenizer`
    for descriptions of the arguments.
    """
    tokenizer = RegexpTokenizer(pattern, gaps, discard_empty, flags)
    return tokenizer.tokenize(text)

blankline_tokenize = BlanklineTokenizer().tokenize
wordpunct_tokenize = WordPunctTokenizer().tokenize


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)

