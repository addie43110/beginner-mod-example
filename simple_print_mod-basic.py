import mod
import sys
import math
import re

from argparse import ArgumentParser
from mod import DG, DGPrinter
from typing import Tuple, List
from prettify import header, blue, green, red, warn, bold, underline
from pathlib import Path

from os import listdir, path

def parse_args():
    parser = ArgumentParser(
                description='Simple mod printing')

    parser.add_argument('input_directory', help="Directory containing the molecules and known reactions "
                                                "with 'graphs' subfolder containing molecules in GML and "
                                                "'rules' subfolder with rules in GML.")
    parser.add_argument('-r', '--repeat', help="number of repeats", default=1)
    parser.add_argument('-m', '--mod_print', action="store_true", help="Create out documents for mod_post.", default=False)
    parser.add_argument('-v', '--verbose', action="store_true", default=False)
    return parser.parse_args(sys.argv[1:])

def load_graphs_and_rules(input_dir):
    graph_folder = path.join(input_dir, "graphs")
    rule_folder = path.join(input_dir, "rules")

    graphs = []
    for file_name in listdir(graph_folder):
        if ".gml" not in file_name: continue
        try:
            graph = mod.Graph.fromGMLFile(path.join(graph_folder, file_name))
            graph.name = file_name[:-4]
            isomorphic_graphs = any([graph.isomorphism(x)for x in graphs])
            if not isomorphic_graphs:
                graphs.append(graph)
        except mod.libpymod.InputError:
            print(warn(f"{file_name} is not connected. Continuing."))

    rules = [mod.Rule.fromGMLFile(path.join(rule_folder, file_name))
                for file_name in listdir(rule_folder) if 'gml' in file_name]

    return (graphs, rules)

def main():
    args = parse_args()
    (graphs, rules) = load_graphs_and_rules(args.input_directory)

    print(f"Imported {red(len(graphs))} graph(s) and {red(len(rules))} rule(s).")

    if args.mod_print:
        mod.post.summarySection("Input graphs")
        for g in graphs:
            g.print()

        mod.post.summarySection("Input rules")
        counter = 0
        for r in rules:
            print(f"printing rule_{counter}: {warn(r.name)}")
            r.print()
            counter+=1

    # generic strat
    strat = (
        mod.addSubset(graphs)
        >> mod.repeat[int(args.repeat)] (
            rules
        )
    )

    dg = DG(graphDatabase=graphs)
    dg.build().execute(strat)

    print(f"Derivation graph has {red(dg.numVertices)} molecule(s) and {red(dg.numEdges)} reaction(s).")
    p = DGPrinter()
    p.withRuleName = True
    """ # hide "small" molecules, those with < 3 atoms
    p.pushVertexVisible(lambda v: v.graph.numVertices > 3)
    # hide the reactions (edges) including the small molecules
    def edgePred(e):
        if any(v.graph.numVertices <= 3 for v in e.sources): return False
        if any(v.graph.numVertices <= 3 for v in e.targets): return False
        return True
    p.pushEdgeVisible(edgePred) """
    dg.print(p)

    if args.mod_print:
        mod.post.summarySection("Products")
        for prod in dg.createdGraphs:
            prod.print()

if __name__=="__main__":
    main()


