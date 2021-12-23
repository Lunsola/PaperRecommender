import numpy as np
import pandas as pd
import networkx as nx
#import math
import shutil
#from tkinter import Tk
from tkinter.filedialog import askdirectory
import os
#from pathlib import Path
import matplotlib.pyplot as plt
import assign_reference_score
import parse_pdf

def stopCheck(old_picks, new_picks):
    '''
    Compares current steps picks with previous steps and checks their similarity

    :param old_picks: Ordered list of all the picks from the previous step
    :param new_picks: Ordered list of all the picks from the current step
    :return: Boolean of whether the program should stop
    '''
    sim = 0
    early_weight = 10

    for n in new_picks:
        loc = new_picks.index(n)
        match = old_picks.index(n) if n in old_picks else None
        if match:
            sim = sim + abs(match - loc)*early_weight
        else:
            sim = sim + 10*early_weight
        early_weight = early_weight - 1

    if set(new_picks[0:2]) == set(old_picks[0:2]):
        sim = 0

    if sim < 250:
        return False
    else:
        return True


def pdfPicker(in_pdfs = None, out_xmls = None, Test = False):
    '''
    Reports list of recommended readings at every step and returns a final network graph

    :param in_pdfs: Folder path in which PDFs will be added at each step
    :param out_xmls: Folder path in which XML files will be generated and PDFs moved to
    :return: Network graph of readings with more than two edges
    '''
    if in_pdfs:
        pdfs = in_pdfs
    else:
        pdfs = askdirectory(title='PDF folder')
    if out_xmls:
        fl = out_xmls
    else:
        fl = askdirectory(title='XML output folder')
    loc_df = None
    G = nx.DiGraph()
    cont = True
    old_picks = []

    while cont:
        file = os.listdir(pdfs)
        parse_pdf.pdf_to_xml(pdfs, fl)
        file_loc = str(fl) + '/' + os.path.splitext(file[0])[0]
        loc_df, G, pick = assign_reference_score.ref_score(file_loc + '.tei.xml', G, loc_df)
        new_picks = pick[0:10].index.tolist()
        print(new_picks[0:3])
        if Test:
            pick['rank'] = np.arange(len(pick))
            print(pick[['score', 'rank']].head())
            scatter = pick.plot.scatter(x='hit_y', y='score', c='DarkBlue')
            scatter.set(xlabel='Raw Hit Count', ylabel='Score')
            plt.show()
            plt.pause(2)
            plt.savefig(file_loc + '.png')
            plt.close()
            samp = pick.sample(n=10)[['score', 'rank']]
            print(samp)
        shutil.move(str(pdfs) + '/' + file[0], str(fl) + '/' + file[0])
        cont = stopCheck(old_picks, new_picks)
        old_picks = new_picks
        if cont:
            input("Press enter when new pdf is ready")

    f = nx.DiGraph()
    fedges = filter(lambda x: G.degree()[x[0]] > 1 and G.degree()[x[1]] > 1, G.edges())
    f.add_edges_from(fedges)

    name2num = {name: num + 1 for num, name in enumerate(list(f.nodes))}
    f = nx.relabel_nodes(f, mapping=name2num, copy=True)

    fig, ax = plt.subplots()
    nx.draw(f, with_labels=True)

    legend_text = "\n".join(f"{v} - {k}" for k, v in name2num.items())
    props = dict(boxstyle="round", facecolor="w", alpha=0.5)
    plt.text(.75, .5, legend_text, fontsize=10, verticalalignment="bottom", bbox=props, transform=ax.transAxes)
    plt.show()

    return f