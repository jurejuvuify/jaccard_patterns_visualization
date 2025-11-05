import verovio
import pandas as pd
import numpy as np
import itertools
import os

# === CONFIGURATION ===
USER_FILES = [
    ("/Users/jurejuvan/PycharmProjects/PythonProject/User_Excel_Files/User36_standardized.xlsx", 36),
    ("/Users/jurejuvan/PycharmProjects/PythonProject/User_Excel_Files/User46_standardized.xlsx", 46),
    ("/Users/jurejuvan/PycharmProjects/PythonProject/User_Excel_Files/User48_standardized.xlsx", 48),
    ("/Users/jurejuvan/PycharmProjects/PythonProject/User_Excel_Files/User49_standardized.xlsx", 49),
    ("/Users/jurejuvan/PycharmProjects/PythonProject/User_Excel_Files/User51_standardized.xlsx", 51),
]

MUSICXML_DIR = "/Users/jurejuvan/PycharmProjects/PythonProject/Split_Songs"
OUTPUT_ROOT = "Jaccard_SVGs_by_UserPair"
os.makedirs(OUTPUT_ROOT, exist_ok=True)


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


# === LOAD USER DATA ===
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
xml_user_map = df.groupby("xml_norm")["user_id"].apply(set).to_dict()

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

    if not os.path.exists(xml_path):
        print(f"⚠️ Skipping missing XML: {xml_filename}")
        continue

    print(f"\n🎼 Processing: {xml_filename}")
    tk = setup_verovio()
    tk.loadFile(xml_path)
    num_pages = tk.getPageCount()

    if num_pages == 0:
        print(f"⚠️ No pages rendered for {xml_filename}. Adjusting settings...")
        tk.setOptions({"scale": 40, "pageWidth": 2000, "pageHeight": 2800})
        tk.loadFile(xml_path)
        num_pages = tk.getPageCount()

    if xml_norm not in xml_user_map:
        print(f"⚠️ No user data found for {xml_filename} — neutral rendering.")
        users_in_xml = set()
    else:
        users_in_xml = xml_user_map[xml_norm]

    print(users_in_xml)

    # === PROCESS EACH USER PAIR ===
    for u1, u2 in user_pairs:
        pair_dir = os.path.join(OUTPUT_ROOT, f"{u1}_{u2}", xml_norm)
        os.makedirs(pair_dir, exist_ok=True)

        j = jaccard(users_in_xml & {u1, u2}, {u1, u2})

        # Normalize single Jaccard value (for uniformity)
        val = float(j)
        r = int(255 * val)
        g = int(255 * val)
        b = int(255 * (1 - val))
        color_pair = f"rgb({r},{g},{b})"

        # Reload clean version of XML for each pair
        tk.loadFile(xml_path)

        # Apply color globally (all measures)
        mei_str = tk.getMEI()
        if users_in_xml:
            print(f"✅ Found user data for {xml_filename} (Jaccard={val:.2f})")
        else:
            print(f"⚪ Rendering {xml_filename} neutral — no user data match.")

        # Render pages
        for page in range(1, num_pages + 1):
            svg = tk.renderToSVG(page)
            svg_path = os.path.join(pair_dir, f"page_{page}.svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)

        print(f"✅ Exported {num_pages} SVG pages for user pair {u1}-{u2} ({xml_norm})")

print("\n🎵 Done! Check your folder:", OUTPUT_ROOT)