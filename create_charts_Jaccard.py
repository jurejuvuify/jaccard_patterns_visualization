import random
import os
import verovio as vrv  # Not used in this script, but kept from your original
import bs4  # <-- ADDED IMPORT
import numpy as np  # <-- ADDED IMPORT
import pandas as pd

# Constants from your script
minWidth = 100
minHeight = 500
minTextWidth = 1500
minTextHeight = 600
system_start = 1025
textline_start = 2408
system_height = 2255


def get_text_y(rect):
    rect_center_y = max((rect[1] + (rect[3] // 2)) - 1025, 0)
    indx = int(rect_center_y // system_height)
    return textline_start + indx * system_height


def contains_same_location(locations, new_location):
    for loc in locations:
        if abs(loc[0] - new_location[0]) < 2 * max(minTextWidth, loc[2]) and abs(
                loc[1] - new_location[1]) < minTextHeight:
            return True, loc
    return False, None


def generate_analysis():
    # --- PRE-REQUISITE ---
    # This folder 'output_svgs_mei' MUST exist and be filled with
    # the SVG files of your scores (e.g., "001_song_1.svg", "002_song_2.svg")
    # ---------------------
    try:
        song_files = os.listdir('Song_Excel_Files_MARIJA (SVG)')
        if not song_files:
            print("Error: The 'Song_Excel_Files_MARIJA (SVG)' folder is empty.")
            print("Please fill it with your pre-rendered SVG score files.")
            return
    except FileNotFoundError:
        print("Error: Folder 'Song_Excel_Files_MARIJA (SVG)' not found.")
        print("Please create this folder and fill it with your pre-rendered SVG score files.")
        return

    try:
        patterns = pd.read_csv('PatternVsi (standardized).csv')
    except FileNotFoundError:
        print("Error: 'PatternVsi (standardized).csv' not found.")
        return

    # Create output directories
    os.makedirs('songs', exist_ok=True)
    os.makedirs('results', exist_ok=True)  # <-- ADDED

    for song_id in range(22):
        song_patterns = patterns[patterns['song_id'] == song_id].copy()

        # --- FIX ---
        # Removed the 'users' filter to process all users
        # song_patterns = song_patterns[song_patterns['user_id'].isin(users)]
        # -----------

        if song_patterns.empty:
            print(f"--- Song {song_id}: No patterns found. Skipping. ---")
            continue

        if (not os.path.exists('songs/{}'.format(song_id))):
            os.makedirs('songs/{}'.format(song_id))

        song_paths = [f for f in song_files if f.startswith(f"{song_id:03d}")]  # Assumes file naming like 001_...svg
        if not song_paths:
            song_paths = [f for f in song_files if f.startswith(f"song_{song_id}")]  # Fallback naming

        print("---------------------------------------------------")
        print(f"Processing Song {song_id}. Found {len(song_patterns)} patterns.")
        if not song_paths:
            print(f"Warning: No SVG file found for song {song_id} in 'output_svgs_mei'. Skipping.")
            continue

        not_found_ids = []
        found_ids = []

        for song_path in song_paths:
            print(f"  > Loading SVG: {song_path}")
            try:
                svg_output = open(os.path.join('output_svgs_mei', song_path), 'r', encoding='utf-8').read()
            except Exception as e:
                print(f"    > Error reading SVG: {e}")
                continue

            colors = ['#ff0000', '#00ff00', '#0000ff', '#800080', '#008000', '#800000', '#000080', '#008080', '#800000',
                      '#2596be', '#FF9333', '#FF33AB', '#BB33FF', '#2CE1A5', '#CDD136', '#D1AF36', '#D18136']
            lenCol = len(colors)
            categories = song_patterns['pattern_tag'].unique()

            # This visualizes SIMILARITY OF TAG
            for i, category in enumerate(categories):
                song_patterns.loc[song_patterns['pattern_tag'] == category, 'color'] = colors[i % lenCol]

            # --- FIX ---
            # This line was unused and 'users' is undefined
            # user_colors = {user: colors[user % len(colors)] for user in users}
            # -----------

            svg_soup = bs4.BeautifulSoup(svg_output, 'xml')
            page_margin = svg_soup.find('g', attrs={'class': 'page-margin'})

            if not page_margin:
                print(f"    > Warning: Could not find <g class='page-margin'> in {song_path}.")
                print("    > Annotations will be skipped. Is this a Verovio SVG?")
                continue

            obj_locs = []
            for i, row in song_patterns.iterrows():
                user = row['user_id']
                # Use 'color' from the DataFrame (set by pattern_tag)
                pattern_color = row.get('color', '#000000')

                soup = bs4.BeautifulSoup(row['xml_file'], 'xml')
                notes = soup.find_all('note')
                if not notes:
                    continue

                first_note = notes[0]
                last_note = notes[-1]
                first_id = first_note.get('xml:id')
                last_id = last_note.get('xml:id')

                if not first_id or not last_id:
                    continue

                first_note_obj = svg_soup.find('g', id=first_id)
                last_note_obj = svg_soup.find('g', id=last_id)

                # ... (rest of your drawing logic, which is complex) ...
                # This logic is kept exactly as you provided it

                s1 = first_note_obj.find('use') if first_note_obj else None
                sx1 = int(s1['x']) - 50 - user - random.randint(0, 50) if s1 else 0
                sy1 = int(s1['y']) - 100 - random.randint(0, 100) if s1 else 0

                s2 = last_note_obj.find('use') if last_note_obj else None
                sx2 = int(s2['x']) if s2 else 20300
                sy2 = int(s2['y']) if s2 else sy1

                if not first_note_obj and not last_note_obj:
                    continue

                if not first_note_obj or not last_note_obj:
                    if first_note_obj:
                        found_ids.append(first_id)
                        page_margin.append(bs4.BeautifulSoup(
                            f'<rect fill="none" height="{str(minHeight)}" stroke="{pattern_color}" width="{str(20300 - sx1)}" x="{str(sx1)}" y="{sy1}" stroke-width="50"/>',
                            'xml').rect)
                        text_x = 20300  # Centered horizontally
                        text_y = sy1
                        text = bs4.BeautifulSoup(f'''
                            <text x="{text_x}" y="{text_y}" font-weight="bold" font-size="150" fill="{pattern_color}" text-anchor="middle">
                                {row['pattern_tag']} ({row['pattern_rank']})
                            </text>
                        ''', 'xml')
                        page_margin.append(text)
                    if last_note_obj:
                        found_ids.append(last_id)
                        page_margin.append(bs4.BeautifulSoup(
                            f'<rect fill="none" height="{str(minHeight)}" stroke="{pattern_color}" width="{str(sx2 + 300)}" x="-300" y="{sy1}" stroke-width="50"/>',
                            'xml').rect)
                        text_x = -300
                        text_y = sy2
                        text = bs4.BeautifulSoup(f'''
                            <text x="{text_x}" y="{text_y}" font-weight="bold" font-size="150" fill="{pattern_color}" text-anchor="middle">
                                {row['pattern_tag']} ({row['pattern_rank']})
                            </text>
                        ''', 'xml')
                        page_margin.append(text)
                    continue

                not_found_ids = [x for x in not_found_ids if x != last_id and x != first_id]
                found_ids.append(first_id)
                found_ids.append(last_id)

                width = max(abs(int(sx2) - int(sx1) + 200 + random.randint(0, 100)), minWidth)
                height = max(abs(int(sy2) - int(sy1) + 100 + random.randint(0, 100)), minHeight)
                rects = []

                if height > 1700:
                    x1 = int(sx1)
                    y1 = int(sy1)
                    height1 = height // 3
                    isOk = False
                    while not isOk:
                        ok, loc = contains_same_location(obj_locs, (x1, y1, 20000 - x1 + 300))
                        if not ok and loc is not None:
                            y1 = y1 + minTextHeight
                        else:
                            isOk = True
                            obj_locs.append((x1, y1, 20000 - x1 + 300))
                            obj_locs.append((x1, y1 + height1, 20000 - x1))
                    rects.append((x1, y1, 20000 - x1 + 300, height1))
                    if height > 2 * 2000:
                        for r in range(height // 1300 - 1):
                            rects.append((-300, y1 + 1300, 20600, height1))
                    isOk = False
                    x2 = 0
                    y2 = int(sy2) - height1 // 2
                    height2 = height1
                    while not isOk:
                        ok, loc = contains_same_location(obj_locs, (x2, y2, sx2 + 200))
                        if not ok and loc is not None:
                            y2 = y2 + minTextHeight
                        else:
                            isOk = True
                            obj_locs.append((x2 - 300, y2, sx2 + 200))
                            obj_locs.append((x2 - 300, y2 + height2, sx2 + 200))
                    rects.append((x2 - 300, y2, sx2 + random.randint(0, 100) + 200 + 300, height2))
                else:
                    isOk = False
                    while not isOk:
                        ok, loc = contains_same_location(obj_locs, (sx1, sy1, width))
                        if not ok and loc is not None:
                            sy1 = sy1 + minTextHeight
                        else:
                            isOk = True
                            obj_locs.append((sx1, sy1, width))
                            obj_locs.append((sx1, sy1 + height, width))
                    rects.append((int(sx1), int(sy1), width, height))

                for rect in rects:
                    page_margin.append(bs4.BeautifulSoup(
                        f'<rect fill="none" height="{str(max(rect[3], minHeight))}" stroke="{pattern_color}" width="{str(max(rect[2], minWidth))}" x="{str(rect[0])}" y="{rect[1]}" stroke-width="50"/>',
                        'xml').rect)
                    text_x = rect[0] + 400
                    offset = np.random.randint(100, 200)
                    text_y = max(get_text_y(rect) + offset, rect[1] + rect[3] + 200)
                    y_ok = False
                    while not y_ok:
                        is_ok, loc = contains_same_location(obj_locs, (text_x, text_y))
                        if not is_ok and loc is not None:
                            text_y = text_y - minTextHeight
                        else:
                            y_ok = True
                            obj_locs.append((text_x, text_y, minTextWidth))

                    text = bs4.BeautifulSoup(f'''
                        <text x="{text_x}" y="{text_y}" font-weight="bold" font-size="150" fill="{pattern_color}" text-anchor="middle">
                            {row['pattern_tag']} ({row['pattern_rank']})
                        </text>
                    ''', 'xml')
                    page_margin.append(text)

            song_name = song_path.split('.')[0]
            # --- FIX ---
            # Removed the `users` variable from the output name
            path = os.path.join('results', f'{song_name}_annotated.svg')
            # -----------

            with open(path, 'w', encoding='utf-8') as f:
                f.write(svg_soup.prettify())
            print(f"  > Saved annotated SVG: {path}")

        not_found_ids = [x for x in not_found_ids if not (x in found_ids)]
        print("not found ids", len(not_found_ids))
        if len(not_found_ids) > 0:
            print(not_found_ids)


# --- FIX ---
# Added this block to actually run the script
if __name__ == "__main__":
    generate_analysis()