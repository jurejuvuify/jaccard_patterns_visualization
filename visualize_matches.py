import json
import random
import os

import bs4
import verovio as vrv
minWidth = 100
minHeight = 500
import pandas as pd
minTextWidth = 1500
minTextHeight = 600
system_start = 1025
textline_start = 2408
line_height = 1000
system_height = 2255 ## we want that all text is below its designated system - > we will determine the center y of rectangle and accordingly set the y of text
output_folder = "visualization_results"
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

def divide_patterns(patterns):
   result = []
   sorted_patterns = sorted(patterns, key=lambda p: len(p[0]), reverse=True)

   for p in sorted_patterns:
       found_place = False
       notes, tag, id = p
       if len(result) > 0:
           for i in range(len(result)):
               # todo malo popravi
               r = result[i]
               notes_in_result = [ni for n, _, _ in r for ni in n]
               if all([n not in notes_in_result for n in notes]):
                   result[i].append(p)
                   found_place = True
                   break
       if not found_place:
           result.append([p])
   return result

def fill_pat_list(matches, ids, n):
   pats = []
   added = set()
   for m in matches:

       if m[n][2] in ids and m[n][2] not in added:
           pats.append(m[n])
           added.add(m[n][2])
   return pats

def visualize_matches(matches):
   song_files = os.listdir('output_svgs_mei')
   with open(matches, 'r') as f:
       matches_data = json.load(f)
   song_id, user1, user2 = os.path.basename(matches).split('_')
   user2 = user2.split('.')[0]
   colors = {
       user1: 'red',
       user2: 'blue',
       intersect: 'green',
       contained: 'violet',
   }

   song_paths = [f for f in song_files if int(f[:3]) == int(song_id)]
   for song_path in song_paths:
       svg_output = open(os.path.join('output_svgs_mei', song_path), 'r').read()

       svg_soup = bs4.BeautifulSoup(svg_output, 'xml')
       page_margin = svg_soup.find('g', attrs={'class': 'page-margin'})
       obj_locs = []
       if (not os.path.exists(f'{output_folder}/{song_id}')):
           os.makedirs(f'{output_folder}/{song_id}')

       pats_us1_ids = {p1[2] for p1, p2, matchtype in matches_data}
       pats_us1 = fill_pat_list(matches_data, pats_us1_ids, 0)
       pats_us2_ids = {p2[2] for p1, p2, matchtype in matches_data}
       pats_us2 = fill_pat_list(matches_data, pats_us2_ids, 1)

       pat1_pages = divide_patterns(pats_us1)
       pat2_pages = divide_patterns(pats_us2)
       print(len(pat1_pages), len(pat2_pages))

       for i, pat1_page in enumerate(pat1_pages):
           for j, pat2_page in enumerate(pat2_pages):
               svg_output = open(os.path.join('output_svgs_mei', song_path), 'r').read()
               svg_soup = bs4.BeautifulSoup(svg_output, 'xml')
               page_margin = svg_soup.find('g', attrs={'class': 'page-margin'})
               for match in matches_data:
                   pat1, pat2, match_type = match
                   if pat1 not in pat1_page:
                       continue
                   if pat2 not in pat2_page:
                       continue

                   notes1, tag1, id1 = pat1
                   notes2, tag2, id2 = pat2

                   first_note = None
                   last_note = None

                   first_notes = [notes1[0], notes2[0]]
                   last_notes = [notes1[1], notes2[1]]

                   for noteid in notes1:
                       note_obj = svg_soup.find('g', id=noteid)
                       if note_obj is None:
                           continue
                       color = ''
                       if noteid not in notes2:
                           #user1 color
                           color = colors[user1]
                       elif match_type == intersect:
                           # green
                           color = colors[intersect]
                       else:
                           # violet
                           color = colors[contained]

                       note_obj['color'] = color
                       head = note_obj.find('g', class_='notehead')
                       if head is not None:
                           head['fill'] = color
                           if noteid in first_notes or noteid in last_notes:
                               use = head.find('use')
                               if use is not None:
                                   x = float(use['x'])
                                   y = float(use['y'])
                                   # we need to check if it is in the same row or not
                                   if first_note is None:
                                       first_note = (x, y)
                                   elif noteid in first_notes:
                                       xi, yi = first_note
                                       if (x < xi and abs(float(y) - float(yi))<line_height) or (float(y) < float(yi) - line_height):
                                           first_note = (x, y)
                                   if last_note is None:
                                       last_note = (x, y)
                                   elif noteid in last_notes:
                                       xi, yi = last_note
                                       if (x>xi and abs(float(y) - float(yi))<line_height) or (float(y) > yi - line_height):
                                           last_note = (x, y)
                   for noteid in pat2:
                       if noteid not in pat1:
                           note_obj = svg_soup.find('g', id=noteid)
                           if note_obj is None:
                               continue
                           color = colors[user2]

                           note_obj['color'] = color
                           head = note_obj.find('g', class_='notehead')
                           if head is not None:
                               head['fill'] = color
                               use = head.find('use')
                               if use is not None:
                                   x = float(use['x'])
                                   y = float(use['y'])
                                   # we need to check if it is in the same row or not
                                   if first_note is None:
                                       first_note = (x, y)
                                   elif noteid in first_notes:
                                       xi, yi = first_note
                                       if (x < float(xi) and abs(float(y) - float(yi)) < line_height) or (
                                               float(y) < float(yi) - line_height):
                                           first_note = (x, y)
                                   if last_note is None:
                                       last_note = (x, y)
                                   elif noteid in last_notes:
                                       xi, yi = last_note
                                       if (x > float(xi) and abs(float(y) - float(yi)) < line_height) or (
                                               float(y) > yi - line_height):
                                           last_note = (x, y)
                   if first_note and last_note:
                       # Create the first line tag (for the start note)
                       y1_start = str(float(first_note[1]) - 250)
                       y1_end = str(float(first_note[1]) + 250)

                       start_line_tag = svg_soup.new_tag(
                           'line',
                           attrs={
                               'x1': str(first_note[0]),  # Ensure all attributes are strings
                               'y1': y1_start,
                               'x2': str(first_note[0]),
                               'y2': y1_end,
                               'style': 'stroke:black;stroke-width:20'
                           }
                       )
                       page_margin.append(start_line_tag)
                       text1 = svg_soup.new_tag(
                           'text',
                           attrs={
                               'x': str(last_note[0]),
                               'y': y1_start,
                               'fill': 'green',
                               'font-size': '100pt'
                           }
                       )
                       text1.string = match_type + ' ' + pat1[1] + ' ' + pat2[1]
                       page_margin.append(text1)
                       # Create the second line tag (for the end note)
                       y2_start = str(float(last_note[1]) - line_height//2)
                       y2_end = str(float(last_note[1]) + line_height//2)

                       end_line_tag = svg_soup.new_tag(
                           'line',
                           attrs={
                               'x1': str(last_note[0] + 250),
                               'y1': y2_start,
                               'x2': str(last_note[0] + 250),
                               'y2': y2_end,
                               'style': 'stroke:black;stroke-width:20'
                           }
                       )
                       page_margin.append(end_line_tag)
                       text2 = svg_soup.new_tag(
                           'text',
                           attrs={

                               'x': str(last_note[0] + 250),
                               'y': y2_end,
                               'fill': 'blue',
                               'font-size': '100pt'
                           }
                       )
                       text2.string = match_type + ' ' + pat1[1] + ' ' + pat2[1]
                       page_margin.append(text2)
               song_name = song_path.split('.')[0]
               if not os.path.exists(output_folder):
                   os.makedirs(output_folder)
               path = os.path.join(output_folder, f'{song_name}_{user1}_{user2}_{i}_{j}.svg')

               with open(path, 'w') as f:
                   f.write(svg_soup.prettify())

if __name__ == '__main__':
   path = 'results/0_36_46.json'
   visualize_matches(path)

