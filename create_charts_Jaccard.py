import verovio
import pandas as pd
import numpy as np
import itertools
import os

# === CONFIGURATION ===
USER_FILES = [
    ("./User_Excel_Files/User36_standardized.xlsx", 36),
    ("./User_Excel_Files/User46_standardized.xlsx", 46),
    ("./User_Excel_Files/User48_standardized.xlsx", 48),
    ("./User_Excel_Files/User49_standardized.xlsx", 49),
    ("./User_Excel_Files/User51_standardized.xlsx", 51),
]

MUSICXML_DIR = "./Split_Songs"
OUTPUT_ROOT = "Jaccard_SVGs_by_UserPair"
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# --- CONFIGURABLE PARAMETER ---
NEIGHBORHOOD_SIZE = 2  # Allows similarity credit for patterns starting within +/- 2 measures


# === HELPER FUNCTIONS ===
def normalize_xml_name(name):
    """Normalize XML identifiers for consistent matching."""
    return os.path.splitext(os.path.basename(str(name).strip().lower()))[0]


def setup_verovio():
    """Initialize Verovio toolkit with base options."""
    tk = verovio.toolkit()
    tk.setOptions({
        "pageWidth": 2100,
        "pageHeight": 2970,
        "scale": 50,
        "adjustPageHeight": True
    })
    return tk


def jaccard(set_a, set_b):
    """Compute Jaccard similarity."""
    if not set_a and not set_b:
        return 0
    return len(set_a & set_b) / len(set_a | set_b)


def expand_measures(measure_set, neighborhood_size):
    """
    Expands a set of measures to include neighbors within a specified range,
    used to calculate a 'Neighborhood Jaccard Similarity'.
    """
    expanded_set = set()
    for measure in measure_set:
        for i in range(-neighborhood_size, neighborhood_size + 1):
            if measure + i > 0:
                expanded_set.add(measure + i)
    return expanded_set


# === LOAD AND PROCESS USER DATA ===
df_list = []
for path, uid in USER_FILES:
    if os.path.exists(path):
        temp = pd.read_excel(path)
        temp["user_id"] = uid
        df_list.append(temp)
    else:
        print(f"⚠️ Missing file: {path}")

if not df_list:
    raise FileNotFoundError("No valid user Excel files found!")

df = pd.concat(df_list, ignore_index=True)
df = df.drop(columns=[col for col in df.columns if "pattern_tag" in col], errors="ignore")
df.columns = [c.lower() for c in df.columns]

if "xml_file" not in df.columns:
    raise ValueError("Expected column 'xml_file' in all user files!")

# Normalize XML names for consistent lookup
df["xml_norm"] = df["xml_file"].apply(normalize_xml_name)

# --- Extract Annotated Measures ---
xml_user_measures_map = {}
for xml_norm, group_df in df.groupby("xml_norm"):
    user_measures = {}
    for user_id, user_group in group_df.groupby("user_id"):
        # CRITICAL ASSUMPTION: 'start_measure' is the column name for the pattern's starting measure
        if 'start_measure' in user_group.columns:
            measures = user_group["start_measure"].dropna().astype(int).tolist()
            user_measures[user_id] = set(measures)

    xml_user_measures_map[xml_norm] = user_measures
# -----------------------------------

users = sorted(df["user_id"].unique())
user_pairs = list(itertools.combinations(users, 2))

# === MUSICXML LIST ===
musicxml_files = [
    "000_Bach_-_Cantata_BWV_1_Mvt_6_horn.xml",
    "001_Bach_-_Cantata_BWV_2_Mvt_6_Soprano.xml",
    "002_Beethoven_-_String_Quartet_Op_18_No_1_Violin_I.xml",
    "003_Haydn_-_String_Quartet_Op_74_No_1.xml",
    "004_Mozart_-_Quartet_No_2_in_D_Major_K_155.xml",
    "005_Mozart_-_String_Quartet_K_458_Violin_I.xml",
    "006_Folksong_Compilation_1.xml",
    "007_Folksong_Compilation_2.xml",
    "008_Folksong_Compilation_3.xml",
    "009_Folksong_Compilation_4.xml",
    "010_Folksong_Compilation_5.xml",
    "011_Bob_Berg_-_Angles.xml",
    "012_Lester_Young_-_Body_and_Soul.xml",
    "013_Charlie_Parker_-_Donna_Lee.xml",
    "014_John_Coltrane_-_Impressions_1963.xml",
    "015_Charlie_Parker_-_My_Little_Suede_Shoes.xml",
    "016_Sonny_Rollins_-_Blue_Seven.xml",
    "017_Bach_-_Fugue_No_20_BWV_889.xml",
    "018_Beethoven_-_Sonata_Op_2_No_1_Mvt_3.xml",
    "019_Choppin_-_Mazurka_Op_24_No_4.xml",
    "020_Orlando_Gibbons_-_The_Silver_Swan_1612.xml",
    "021_Mozart_-_Sonata_K_282_Mvt_2.xml"
]

# === PROCESS EACH MUSICXML ===
for xml_filename in musicxml_files:
    xml_path = os.path.join(MUSICXML_DIR, xml_filename)
    xml_norm = normalize_xml_name(xml_filename)
    print("=======================================================================================")

    if not os.path.exists(xml_path):
        print(f"⚠️ Skipping missing XML: {xml_filename}")
        continue

    print(f"\n🎼 Processing: {xml_filename}")

    song_measures_map = xml_user_measures_map.get(xml_norm, {})

    # --- Initial Verovio Setup (No highlights yet) ---
    tk = setup_verovio()
    tk.loadFile(xml_path)
    num_pages = tk.getPageCount()
    if num_pages == 0:
        print(f"⚠️ No pages rendered for {xml_filename}. Adjusting settings...")
        tk.setOptions({"scale": 40, "pageWidth": 2000, "pageHeight": 2800})
        tk.loadFile(xml_path)
        num_pages = tk.getPageCount()

    # === PROCESS EACH USER PAIR (Modified Inner Loop) ===
    for u1, u2 in user_pairs:
        pair_dir = os.path.join(OUTPUT_ROOT, f"{u1}_{u2}", xml_norm)
        os.makedirs(pair_dir, exist_ok=True)

        # 1. GET MEASURES: Retrieve the set of measures annotated by each user
        measures_u1_raw = song_measures_map.get(u1, set())
        measures_u2_raw = song_measures_map.get(u2, set())

        # 2. CALCULATE NEIGHBORHOOD JACCARD:

        # A. Expand the raw sets based on NEIGHBORHOOD_SIZE
        measures_u1_expanded = expand_measures(measures_u1_raw, NEIGHBORHOOD_SIZE)
        measures_u2_expanded = expand_measures(measures_u2_raw, NEIGHBORHOOD_SIZE)

        # B. Calculate Jaccard on the expanded sets
        jaccard_val = jaccard(measures_u1_expanded, measures_u2_expanded)

        # 3. IDENTIFY HIGHLIGHTS: Use the raw sets for the actual visual intersection
        # We only highlight measures that one user *actually* annotated and the other user
        # *also* annotated or annotated nearby. A simple intersection of raw measures is used
        # to prevent highlighting measures that *neither* user annotated.

        # The measures to highlight will be the measures annotated by U1 that are near a measure annotated by U2, AND vice-versa.
        # This is more complex than a simple raw intersection, so we define a 'highlightable' set:

        # Set of measures annotated by U1 that overlap with U2's expanded set
        intersection_u1 = measures_u1_raw & measures_u2_expanded
        # Set of measures annotated by U2 that overlap with U1's expanded set
        intersection_u2 = measures_u2_raw & measures_u1_expanded

        # The total set of measures that are considered "similar"
        highlight_measures = list(intersection_u1 | intersection_u2)

        # 4. COLORING SCHEME: Based on the new, smoothed Jaccard value

        val = float(jaccard_val)
        # Low similarity (0) = Blue (R:0, G:0, B:255)
        # High similarity (1) = Yellow (R:255, G:255, B:0)
        r_val = int(255 * val)
        g_val = int(255 * val)
        b_val = int(255 * (1 - val))
        highlight_color = f"rgb({r_val},{g_val},{b_val})"

        # 5. APPLY HIGHLIGHTING

        # Reload clean version of XML and reset highlights
        tk.loadFile(xml_path)
        tk.setOptions({"highlighted": []})

        if highlight_measures:
            highlights = []
            # The set of unique measures to highlight (to avoid duplicate IDs)
            unique_highlight_measures = set(highlight_measures)

            for measure_num in unique_highlight_measures:
                mei_id = f"m{measure_num}"

                highlights.append({
                    "id": mei_id,
                    "color": highlight_color,
                    "opacity": 0.5,
                    "fill": True,
                    "region": True
                })

            tk.setOptions({"highlighted": highlights})

            print(
                f"✅ Highlighting {len(unique_highlight_measures)} near-similar measures for {u1}-{u2} (Neighborhood Size={NEIGHBORHOOD_SIZE}). Jaccard={jaccard_val:.4f}")
        else:
            print(
                f"⚪ No similar patterns found, even with neighborhood search for {u1}-{u2}. Jaccard={jaccard_val:.4f}")

        # 6. Render pages
        num_pages = tk.getPageCount()
        for page in range(1, num_pages + 1):
            svg = tk.renderToSVG(page)
            svg_path = os.path.join(pair_dir, f"page_{page}.svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)

        print(f"✅ Exported {num_pages} SVG pages for user pair {u1}-{u2} ({xml_norm})")

print("\n🎵 Done! Check your folder:", OUTPUT_ROOT)