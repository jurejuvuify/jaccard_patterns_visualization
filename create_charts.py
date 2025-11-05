import pandas as pd
import altair as alt
import os
import zipfile

# List of files and user names
files_info = {
    "User 36": "User36.xlsx - Tabelle1.csv",
    "User 46": "User46.xlsx - Tabelle1.csv",
    "User 48": "User48.xlsx - Tabelle1.csv",
    "User 49": "User49.xlsx - Tabelle1.csv",
    "User 51": "User51.xlsx - Tabelle1.csv"
}

# Define the zip file name
zip_file_name = 'all_charts_high_quality.zip'

# To store all loaded dataframes
dfs = {}

try:
    print("Loading data files...")
    # --- 1. Load all data ---
    for user, file_name in files_info.items():
        if not os.path.exists(file_name):
            print(f"!!! ERROR: File not found: {file_name}")
            print("Please make sure all CSV files are in the same directory as this script.")
            exit()
        dfs[user] = pd.read_csv(file_name)
    print("All data loaded successfully.")

    # --- 2. Create Zip File and Add Charts One by One ---
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        print(f"Created '{zip_file_name}'. Adding charts...")

        # --- Chart: User 36 ---
        file_36 = 'user_36_patterns_chart.json'
        data_36 = dfs['User 36']['pattern_tag'].value_counts().reset_index().rename(
            columns={'index': 'Pattern Tag', 'pattern_tag': 'Occurrences'}
        )
        chart_36 = alt.Chart(data_36).mark_bar().encode(
            x=alt.X('Pattern Tag', sort=alt.EncodingSortField(field="Occurrences", op="sum", order='descending')),
            y=alt.Y('Occurrences'),
            tooltip=['Pattern Tag', 'Occurrences']
        ).properties(title='Pattern Occurrences: User 36').interactive()
        chart_36.save(file_36)
        zf.write(file_36)
        os.remove(file_36)
        print(f"Added {file_36}")

        # --- Chart: User 51 ---
        file_51 = 'user_51_patterns_chart.json'
        data_51 = dfs['User 51']['pattern_tag'].value_counts().reset_index().rename(
            columns={'index': 'Pattern Tag', 'pattern_tag': 'Occurrences'}
        )
        chart_51 = alt.Chart(data_51).mark_bar().encode(
            y=alt.Y('Pattern Tag', sort=alt.EncodingSortField(field="Occurrences", op="sum", order='descending')),
            x=alt.X('Occurrences'),
            tooltip=['Pattern Tag', 'Occurrences']
        ).properties(title='Pattern Occurrences: User 51').interactive()
        chart_51.save(file_51)
        zf.write(file_51)
        os.remove(file_51)
        print(f"Added {file_51}")

        # --- Charts: Users 46, 48, 49 ---
        for user_name in ['User 46', 'User 48', 'User 49']:
            chart_file_name = f"{user_name.lower().replace(' ', '_')}_patterns_chart.json"
            data = dfs[user_name]['pattern_tag'].value_counts().reset_index().rename(
                columns={'index': 'Pattern Tag', 'pattern_tag': 'Occurrences'}
            )
            chart = alt.Chart(data).mark_bar().encode(
                y=alt.Y('Pattern Tag', sort=alt.EncodingSortField(field="Occurrences", op="sum", order='descending')),
                x=alt.X('Occurrences'),
                tooltip=['Pattern Tag', 'Occurrences']
            ).properties(title=f'Pattern Occurrences: {user_name}').interactive()

            chart.save(chart_file_name)
            zf.write(chart_file_name)
            os.remove(chart_file_name)
            print(f"Added {chart_file_name}")

        # --- Chart: All Users Comparison ---
        file_all_users = 'all_users_comparison_chart.json'
        summary_data = []
        for user, df in dfs.items():
            summary_data.append({"User": user, "Metric": "Total Occurrences", "Count": len(df)})
            summary_data.append({"User": user, "Metric": "Unique Patterns", "Count": df['pattern_tag'].nunique()})

        summary_df = pd.DataFrame(summary_data)
        chart_all_users = alt.Chart(summary_df).mark_bar().encode(
            x=alt.X('User', axis=None),
            y=alt.Y('Count', title='Count'),
            color=alt.Color('User', title='User'),
            column=alt.Column('Metric', title='Metric', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
            tooltip=['User', 'Metric', 'Count']
        ).properties(title='Pattern Occurrences and Variety by User').interactive()
        chart_all_users.save(file_all_users)
        zf.write(file_all_users)
        os.remove(file_all_users)
        print(f"Added {file_all_users}")

        # --- Chart: Top 20 Standardized ---
        file_standardized = 'top_20_standardized_patterns_chart.json'


        def standardize_tag(tag):
            tag_str = str(tag).lower().strip()
            if tag_str.startswith('sub.vz'): return tag_str[7:]
            if tag_str.startswith('pat-'): return tag_str[4:]
            if tag_str.startswith('vz'): return tag_str[2:]
            if tag_str.startswith('sub-'): return tag_str[4:]
            return tag_str


        all_dfs = []
        for user, df in dfs.items():
            df_copy = df.copy()
            df_copy['User'] = user
            all_dfs.append(df_copy)

        all_data = pd.concat(all_dfs, ignore_index=True)
        all_data['standardized_tag'] = all_data['pattern_tag'].apply(standardize_tag)

        top_20_tags_overall = all_data['standardized_tag'].value_counts().head(20).reset_index()
        top_20_tags_overall.columns = ['Standardized Tag', 'Total Occurrences']  # Renaming for clarity
        top_20_tag_list = top_20_tags_overall['Standardized Tag'].tolist()

        chart_data = all_data[all_data['standardized_tag'].isin(top_20_tag_list)]
        chart_data_grouped = chart_data.groupby(['standardized_tag', 'User']).size().reset_index(name='Occurrences')

        chart_standardized = alt.Chart(chart_data_grouped).mark_bar().encode(
            x=alt.X('standardized_tag', title='Standardized Pattern Tag', sort=top_20_tag_list),
            y=alt.Y('Occurrences', title='Total Occurrences'),
            color=alt.Color('User', title='User'),
            tooltip=['standardized_tag', 'User', 'Occurrences']
        ).properties(title='Top 20 Standardized Patterns by User').interactive()
        chart_standardized.save(file_standardized)
        zf.write(file_standardized)
        os.remove(file_standardized)
        print(f"Added {file_standardized}")

    print(f"\nSuccessfully created '{zip_file_name}' with all 7 charts.")

except Exception as e:
    print(f"An error occurred: {e}")