#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2014 University of Dundee. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Parser for the gene-ontology to OMERO's tag format:

[{
    "name" : "Name of the tagset",
    "desc" : "Description of the tagset",
    "set" : [{
        "name" : "Name of tag",
        "desc" : "Description of tag"
    },{
        "name" : "Name of tag",
        "desc" : "Description of tag"
    }]
}]
"""

import json
import sys

def parse(filename, MAX_TERM_COUNT=1000):
    """
    MAX_TERM_COUNT = 10000       # There are 39,000 terms in the GO!
    """
    terms = {}      # "GO:0000002" : {'name':name, 'def': def, 'children': ['GO:00003', 'GO:00004'...], 'parents': ['GO:000045'...]}
    with open(filename, "r") as f:

        termId = None
        name = None
        desc = None
        parents = []

        termCount = 0
        for l in f.readlines():
            if l.startswith("id:"):
                termId = l.strip()[4:]
            if l.startswith("name:"):
                name = l.strip()[6:]
            elif l.startswith("def:"):
                desc = l.strip()[5:]
            elif l.startswith("is_a:"):
                pid = l.strip()[6:].split(" ", 1)[0]
                parents.append(pid)
            if len(l) == 1:     # newline
                # save
                if termId is not None and name is not None:
                    terms[termId] = {'name':name, 'desc':desc, 'parents': parents[:], 'children':[]}
                    termId = None
                    name = None
                    parents = []
                    termCount += 1
                    if MAX_TERM_COUNT is not None and termCount > MAX_TERM_COUNT:
                        break

    count = 0
    for tid, tdict in terms.items():
        count += 1      # purely for display
        for p in tdict['parents']:
            if p in terms.keys():
                terms[p]['children'].append(tid)

    # Get unique term IDs for Tag Groups.
    tagGroups = set()
    for tid, tdict in terms.items():
        # Only create Tags for GO:terms that are 'leafs' of the tree
        if len(tdict['children']) == 0:
            for p in tdict['parents']:
                tagGroups.add(p)

    return tagGroups, terms


def generate(tagGroups, terms):
    """
    create Tag Groups and Child Tags using data from terms dict
    """

    rv = []
    for pid in tagGroups:
        if pid not in terms.keys():    # In testing we may not have comeplete set
            continue

        groupData = terms[pid]
        groupName = groupData['name']
        groupDesc = groupData['desc']
        children = []
        group = dict(name=groupName, desc=groupDesc, set=children)
        rv.append(group)

        for cid in groupData['children']:
            cData = terms[cid]
            cName = cData['name']
            cDesc = cData['desc']
            child = dict(name=cName, desc=cDesc)
            children.append(child)

    return json.dumps(rv)


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        tagGroups, terms = parse(filename)
        print generate(tagGroups, terms)
