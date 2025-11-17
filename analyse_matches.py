import json
import random
import os
import sys

import bs4
import verovio as vrv
from tqdm import tqdm

minWidth = 100
minHeight = 500
import pandas as pd
minTextWidth = 1500
minTextHeight = 600
system_start = 1025
textline_start = 2408
system_height = 2255 ## we want that all text is below its designated system - > we will determine the center y of rectangle and accordingly set the y of text
output_folder = "Song_Excel_Files_MARIJA (SVG)"
intersect = 'intersect'
contained = 'contained'
contained1in2 = 'contained1in2'
contained2in1 = 'contained2in1'

def get_text_y(rect):
    rect_center_y = max((rect[1] + (rect[3] // 2)) - 1025, 0)
    indx = int(rect_center_y // system_height)
    return textline_start + indx * system_height

def contains_same_location(locations, new_location):
    for loc in locations:
        if abs(loc[0] - new_location[0]) < 2 * max(minTextWidth, loc[2]) and abs(loc[1] - new_location[1]) < minTextHeight:
            return True, loc
    return False, None

def generate_analysis(user1, user2):
    song_files = os.listdir('Song_Excel_Files')
    patterns = pd.read_csv('PatternVsi (standardized).csv')
    # patterns['found'] = False
    # found = 0
    for song_id in tqdm(range(22)):
        song_patterns = patterns[patterns['song_id'] == song_id]
        song_patterns1 = song_patterns[song_patterns['user_id'] == user1]
        song_patterns2 = song_patterns[song_patterns['user_id'] == user2]

        if (not os.path.exists(output_folder + '/' + str(song_id))):
            os.makedirs(output_folder + '/' + str(song_id))

        song_paths = [f for f in song_files if int(f[:3]) == song_id]

        matches = []

        for song_path in song_paths:
            svg_output = open(os.path.join('Song_Excel_Files', song_path), 'r').read()
            svg_soup = bs4.BeautifulSoup(svg_output, 'xml')
            page_margin = svg_soup.find('g', attrs={'class': 'page-margin'})
            colors = {
                user1: 'red',
                user2: 'blue',
                intersect: 'green',
                contained: 'violet',
            }
            for i, pattern in song_patterns1.iterrows():

                soup = bs4.BeautifulSoup(pattern['xml_file'], 'xml')
                notes = soup.find_all('note')
                if not notes:
                    continue
                note_ids = [n['xml:id'] for n in notes if n.has_attr('xml:id')]

                for j, p in song_patterns2.iterrows():
                    soup2 = bs4.BeautifulSoup(p['xml_file'], 'xml')
                    notes2 = soup2.find_all('note')
                    if not notes2:
                        continue
                    note_ids2 = [n['xml:id'] for n in notes2 if n.has_attr('xml:id')]

                    if not any([n in note_ids2 for n in note_ids]):
                        continue

                    mask1 = [n in note_ids2 for n in note_ids]
                    mask2 = [n in note_ids for n in note_ids2]

                    if all(mask1):
                        # prvi je mogoce contained v drugem
                        if mask2[0] or mask2[-1]:
                            # imamo overlap
                            matches.append(((note_ids, pattern['pattern_tag'], i), (note_ids2, p['pattern_tag'], j), intersect))
                        else:
                            matches.append(((note_ids, pattern['pattern_tag'], i), (note_ids2, p['pattern_tag'], j), contained1in2))
                    elif all(mask2):
                        if mask1[0] or mask1[-1]:
                            matches.append(((note_ids, pattern['pattern_tag'], i), (note_ids2, p['pattern_tag'], j), intersect))
                        else:
                            matches.append(((note_ids, pattern['pattern_tag'], i), (note_ids2, p['pattern_tag'], j), contained2in1))
                    else:
                        matches.append(((note_ids, pattern['pattern_tag'], i), (note_ids2, p['pattern_tag'], j), intersect))

            with open(os.path.join('results', f'{song_id}_{user1}_{user2}.json'), 'w') as f:
                json.dump(matches, f)


if __name__ == '__main__':
    users = [36, 46, 48, 49, 51]

    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            print(f'{users[i]} -> {users[j]}')
            generate_analysis(users[i], users[j])
    # generate_analysis(users[0], users[3])

