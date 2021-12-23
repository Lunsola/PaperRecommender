from grobid_client_python.grobid_client.grobid_client import GrobidClient
from bs4 import BeautifulSoup as BS
#import os
from collections import defaultdict
import pandas as pd
import seaborn
import networkx as nx

# on ubuntu: docker run -t --rm --init -p 8070:8070 lfoppiano/grobid:0.7.0
# Some notes on the thing itself https://grobid.readthedocs.io/en/latest/References/

def pdf_to_xml(input, output):
    '''
    Uses GROBID client to parse raw pdf into structured xml document

    :param input: Folder path in which PDFs will be added at each step
    :param output: Folder path in which XML files will be generated and PDFs moved to
    :return: structured XML
    '''

    client = GrobidClient(config_path="./grobid_client_python/config.json")
    client.process("processFulltextDocument", str(input), output=str(output))

def extractRefs(bs_content):
    '''
    Pulls out and assigns names to each reference in bibliography

    :param bs_content: Raw output of structured XML parsing
    :return: List of titles and list of their associated GROBID ids
    '''

    titles = []
    article_codes = []

    try:
        articles = bs_content.find_all('biblstruct')
    except:
        articles = []
        print("Improper xml")

    for i, article in enumerate(articles):
        names = []
        article_codes.append(article.get('xml:id'))
        people = article.find_all('persname')
        for p in people:
            try:
                f_name = p.find('forename', type='first').text
                m_name = p.find('forename', type='middle').text if p.find('forename', type='middle') else ''
                l_name = p.find('surname').text
                name = '{}. {}. {}'.format(f_name, m_name, l_name) if m_name != '' \
                    else '{}. {}'.format(f_name, l_name)
                names.append(name)
            except:
                print("Not enough author name information")
        try:
            titles.append(article.find('title', level='a', type="main").text)
        except:
            if article.find('title', level='m'):
                titles.append(article.find('title', level='m').text)
            else:
                date = article.find('date')['when'] if article.find('date') else "UnknownDate"
                first_author = names[0] if names else "UnknownAuthor"
                titles.append(first_author + '_' + date)

    return titles, article_codes[1:]

def reference_meta(file_loc, G, old_df = None):
    '''
    Derives metrics from GROBID's structured XML output

    :param file_loc: File path to the new PDF
    :param G: Network graph of citations
    :param old_df: Dataframe of previous metrics
    :return: Dataframe of updated metrics and updated Network graph
    '''

    with open(file_loc, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        content = "".join(content)
        bs_content = BS(content, "html5lib")
        bs_content_b = BS(content, "lxml")

    start_node = bs_content.find('title').text
    G.add_node(start_node)

    body = bs_content_b.find("body")

    references = bs_content.find_all("ref")

    titles, art_codes = extractRefs(body)

    locations = []
    prev_loc = [0, 0]
    tot_len = 0
    citation_group = -1
    co_citations = []
    section = []
    title = []

    last_cited = defaultdict(lambda: -99)
    cite_distance = []

    for r in references:
        try:
            if(r.attrs['type']=='bibr'):
                bib_num = r.attrs['target']
                loc = bib_num[2:]
                t = titles[int(loc) + 1]
                locations.append(loc)
                line_num = r.sourceline
                section.append(line_num)
                G.add_node(t)
                G.add_edge(start_node, t)
                title.append(t)
                pos = r.sourcepos
                if line_num == prev_loc[0] and pos - prev_loc[1] < tot_len:
                    pass
                else:
                    citation_group = citation_group + 1
                co_citations.append(citation_group)
                if last_cited[t] == -99:
                    cite_distance.append(0.01)
                else:
                    cite_distance.append(co_citations[-1] - last_cited[t])
                last_cited[t] = co_citations[-1]
                tot_len = 33 + len(bib_num) + len(r.text) + 5 #5 is buffer on slight length variance
                prev_loc = [line_num, pos]
            else:
                pass
        except:
            print("Error at: " + r.text)

    hit = [1] * len(locations)
    loc_dict = {'location': range(0, len(locations)), 'hit': hit, 'bib_number': locations,
                'citation_group': co_citations, 'section': section, 'title': title,
                'spread': cite_distance}
    loc_df = pd.DataFrame(loc_dict)
    groups = max(loc_df['citation_group'])
    loc_df['w_hit'] = loc_df['hit'].div(groups)
    grouped_citations = loc_df.groupby(['citation_group']). \
        apply(lambda x: 1 / (groups*x['citation_group'].count())).reset_index(name='group_weight')
    loc_df = loc_df.merge(grouped_citations, how='left', on='citation_group')

    if old_df is not None:
        loc_df['citation_group'] = loc_df['citation_group'] + max(old_df['citation_group'])
        loc_df = pd.concat((old_df, loc_df))

    return loc_df, G, locations