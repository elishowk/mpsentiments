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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__="elishowk"
__date__ ="$24 févr. 2011 12:23:02$"

import argparse
import yaml
from mpsentiments import *

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A sentiment analyser')
    parser.add_argument("-e", dest="execute")
    args = parser.parse_args()
    print args
    config = yaml.load(open('config.yaml','rU'))

    if args.execute=="classify":
        main(config)
    if args.execute=="export":
        export_chart(config)
