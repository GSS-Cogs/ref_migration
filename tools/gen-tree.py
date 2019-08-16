#!/bin/env python

import rdflib
import argparse
import tempfile

parser = argparse.ArgumentParser(description='Generate inferred class hierarchy as JSON.')
parser.add_argument(
    'ontology',
    help='Input ontology. Imports are followed.')
args = parser.parse_args()
g = rdflib.Graph()
f = rdflib.util.guess_format(args.ontology)
g.parse(args.ontology, format=f)
imports = set()
finished_imports = False
while not finished_imports:
    to_import = set()
    for ont in g.objects(None, rdflib.OWL.imports):
        if str(ont) not in imports:
            to_import.add(str(ont))
    if bool(to_import):
        for ont in to_import:
            if ont.startswith('file:'):
                f = rdflib.util.guess_format(ont)
                g.parse(ont, format=f)
            else:
                g.parse(ont)
            imports.add(ont)
    else:
        finished_imports = True
g.remove((None, rdflib.OWL.imports, None))
ntriples = tempfile.NamedTemporaryFile(suffix='.nt', delete=False)
g.serialize(destination=ntriples, format='ntriples')
ntriples.close()

from owlready2 import *
import json

onto = get_ontology(f'file://{ntriples.name}')
onto.load()
os.remove(ntriples.name)
ntriples.close()
sync_reasoner_pellet(infer_property_values = True)

def hierarchy(c):
    obj = { 'name': c.iri }
    others = set()
    for eq in c.equivalent_to:
        if hasattr(eq, 'iri') and eq.iri.startswith('http://gss-data.org.uk/def/class/'):
            others.add(eq.iri)
    obj['others'] = list(others)
    if Nothing in c.equivalent_to:
        obj['unsat'] = True
    labels = set(c.label)
    if len(labels) > 0:
        obj['label'] = next(iter(labels))
    children = set()
    for sub in set(c.subclasses()):
        if sub.iri.startswith('http://gss-data.org.uk/def/class/'):
            to_add = True
            for eq in sub.equivalent_to:
                if eq in children:
                    to_add = False
                    break
            if to_add:
                children.add(sub)
    if len(children) > 0 :
        obj['children'] = [hierarchy(c) for c in children]
    return obj

print(json.dumps(hierarchy(owl.Thing), indent=2))
