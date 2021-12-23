import numpy as np
import parse_pdf

def ref_score(file_loc, G, loc_df = None):
    '''
    Uses metrics from parse_pdf to calculate scores

    :param file_loc: File path of the new pdf
    :param G: Network graph of inserted papers and their references
    :param loc_df: Dataframe of previous metric values
    :return: Updated dataframe loc_df of metrics and network graph G as well as the sorted scores in pick
    '''
    loc_df, G, locations = parse_pdf.reference_meta(file_loc, G, loc_df)

    loc_df.loc[loc_df['spread'] >= 5, 'spread'] = 5

    score_df = loc_df.groupby(['title']).aggregate({'location': np.min, 'hit': np.sum,
                                                    'group_weight': np.sum, 'section': np.min,
                                                    'spread': np.sum, 'w_hit': np.sum})
    score_df.fillna(0)
    score_df.loc[score_df['spread'] >= 15, 'spread'] = 15
    loc_thresh = min(score_df['section'])
    score_df['bg'] = score_df['section'].apply(lambda x: 1 if int(x) == int(loc_thresh) else 2)

    score_df['score'] = ((score_df['w_hit'] + score_df['group_weight']) / score_df['bg']) * (1 + score_df['spread'] / 5)
    pick = score_df.sort_values('score', ascending=False)

    return loc_df, G, pick