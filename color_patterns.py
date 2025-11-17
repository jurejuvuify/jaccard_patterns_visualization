import pandas as pd
import xml.etree.ElementTree as ET
import os

# --- CONFIGURE YOUR FILES HERE ---

# 1. (REQUIRED) Edit this to point to your *full* music score file for Song 0
FULL_SCORE_FILE = "./Song_Excel_Files/000_Bach_-_Cantata_BWV_1_Mvt_6_horn.xml"  # <-- EDIT THIS

# 2. These should be in the same directory
#    *** UPDATED to read .xlsx files ***
#    Make sure you have the 'openpyxl' library installed: pip install openpyxl
USER36_FILE = "./User_Excel_Files/User36_standardized.xlsx"
USER51_FILE = "./User_Excel_Files/User51_standardized.xlsx"
OUTPUT_FILE = "./Song_Excel_Files (SVG)/000_Bach_-_Cantata_BWV_1_Mvt_6_horn.xml"

# 3. Define the patterns and their colors
#    You can add/change any hex color codes here.
OVERLAPPING_PATTERNS = ['Pat-1', 'Pat-1.1', 'Pat-1.2', 'Pat-2', 'Pat-3']
PATTERN_COLORS = {
    "Pat-1": "#E63946",  # Red
    "Pat-1.1": "#A8DADC", # Light Blue (Replaced F1FAEE)
    "Pat-1.2": "#457B9D", # Darker Blue
    "Pat-2": "#1D3557",  # Darkest Blue
    "Pat-3": "#E76F51",  # Orange/Coral
}

# --- NAMESPACES FOR MEI XML ---
# This is necessary for parsing MEI files correctly.
NAMESPACES = {
    'mei': 'http://www.music-encoding.org/ns/mei',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}

def get_note_id_to_pattern_map():
    """
    Reads both CSVs, finds all overlapping patterns for song 0,
    and returns a dictionary mapping note xml:id's to a pattern_tag.
    """
    try:
        # *** UPDATED to use pd.read_excel() ***
        df36 = pd.read_excel(USER36_FILE)
        df51 = pd.read_excel(USER51_FILE)
    except FileNotFoundError as e:
        print(f"Error: Could not find file. {e}")
        print("Please make sure your .xlsx files are in the same directory as this script.")
        return None
    except ImportError:
        print("Error: The 'openpyxl' library is required to read .xlsx files.")
        print("Please install it by running: pip install openpyxl")
        return None
    except Exception as e:
        print(f"Error reading Excel files: {e}")
        return None

    note_map = {}
    print("Building note map from patterns...")

    def process_df(df, user_id):
        """Helper function to parse a dataframe and add notes to the map."""
        # Filter for song_id 0 and the specific patterns
        df_filtered = df[
            (df['song_id'] == 0) &
            (df['pattern_tag'].isin(OVERLAPPING_PATTERNS))
        ]

        print(f"  Found {len(df_filtered)} pattern instances for User {user_id}...")

        for _, row in df_filtered.iterrows():
            xml_data = row['xml_file']
            pattern_tag = row['pattern_tag']

            try:
                # Parse the XML string from the CSV
                snippet_root = ET.fromstring(xml_data)

                # Find all <note> elements within this snippet
                notes = snippet_root.findall('.//mei:note', NAMESPACES)

                for note in notes:
                    # Get the 'xml:id' of the note
                    note_id = note.get(f"{{{NAMESPACES['xml']}}}id")
                    if note_id:
                        # Add to map. If users overlap on a note,
                        # the last one processed (User 51) will "win".
                        note_map[note_id] = pattern_tag

            except ET.ParseError as e:
                print(f"    Warning: Skipping row. Could not parse XML for User {user_id}, {pattern_tag}. Error: {e}")
            except Exception as e:
                print(f"    Warning: An unexpected error occurred processing a row. {e}")

    # Process both users
    process_df(df36, 36)
    process_df(df51, 51)

    print(f"\nSuccessfully built map with {len(note_map)} unique notes.")
    return note_map

def color_full_score_xml(note_map, full_score_path, output_path):
    """
    Parses the full score, colors notes based on the map, and saves a new file.
    """
    if not os.path.exists(full_score_path):
        print(f"--- !!! ERROR !!! ---")
        print(f"The full score file was not found: '{full_score_path}'")
        print("Please download the full score for Song 0, place it in this directory,")
        print(f"and update the 'FULL_SCORE_FILE' variable at the top of this script.")
        print("---------------------")
        return False

    print(f"Loading full score from '{full_score_path}'...")

    try:
        # Register namespaces to make sure they are preserved on save
        for prefix, uri in NAMESPACES.items():
            ET.register_namespace(prefix, uri)

        # Parse the entire XML file
        tree = ET.parse(full_score_path)
        root = tree.getroot()

        # Find all note elements in the *entire* score
        all_notes = root.findall('.//mei:note', NAMESPACES)

        if not all_notes:
            print("Warning: Found 0 notes in the full score. Are you sure this is a valid MEI file?")
            return False

        print(f"Found {len(all_notes)} total notes in the full score. Now applying colors...")

        colored_note_count = 0
        for note in all_notes:
            note_id = note.get(f"{{{NAMESPACES['xml']}}}id")

            if note_id and note_id in note_map:
                # This note is in one of our patterns!
                pattern_tag = note_map[note_id]
                color = PATTERN_COLORS.get(pattern_tag)

                if color:
                    # Add the color attribute to the note element
                    note.set('color', color)
                    colored_note_count += 1

        # Save the modified tree to a new file
        tree.write(output_path, encoding='UTF-8', xml_declaration=True)

        print(f"\n--- SUCCESS ---")
        print(f"Successfully colored {colored_note_count} notes.")
        print(f"Modified score saved to: '{output_path}'")
        return True

    except ET.ParseError as e:
        print(f"Error: Could not parse the full score file. Is it valid XML/MEI? {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def main():
    note_map = get_note_id_to_pattern_map()
    if note_map:
        color_full_score_xml(note_map, FULL_SCORE_FILE, OUTPUT_FILE)

if __name__ == "__main__":
    main()