# -*- coding: utf-8 -*-
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/gpl.html>.

import re

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")


def tokenize(text):
    """
    Cuts a @text into tokens
    using nltk Treebank tokenizer
    """
    return [token.lower()\
        for token in re.split("\W", text, re.U|re.I|re.M) if not len(token) > 2]