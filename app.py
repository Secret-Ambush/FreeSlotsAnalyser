import streamlit as st
import pandas as pd
import numpy as np
import fitz
from tabula import read_pdf
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageDraw, ImageFont

im = Image.open('assets/App_Icon.png')
image = Image.open("assets/3.png")
width, height = image.size

draw = ImageDraw.Draw(image)
text = "Free Hours Analyser"
font_path = "assets/VastShadow-Regular.ttf"
font_size = 30 
font = ImageFont.truetype(font_path, font_size)
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (width - text_width) / 2
y = (height - text_height) / 2

draw.text((x, y), text, font=font, fill=(0, 0, 0))

flag = True

footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: transparent;
color: white;
text-align: center;
}
</style>
<div class="footer">
<p></p>
<p>Made with ♥️ by Riddhi Goswami</p>
</div>
"""


def remove_header(df):
    try:
        header_row_index = df[df.iloc[:, 0] == 'COM COD'].index[0]
        df = df.drop(index=df.index[:header_row_index]).reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df.drop(index=0).reset_index(drop=True)
    except:
        pass
    return df

def forward_fill_course_details(df, COURSE_NO, COURSE_TITLE, CREDIT):
    df[CREDIT].fillna(method='ffill', inplace=True)
    df[COURSE_NO].fillna(method='ffill', inplace=True)
    df[COURSE_TITLE].fillna(method='ffill', inplace=True)
    return df

def map_days_hours_to_time_slots(day_hour_str):
    # Map shorthand to full day names
    days = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'Th': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'Su': 'Sunday'}
    day_hour_list = []
    day_str = ''
    hour_str = ''
    if isinstance(day_hour_str, str):
        for char in day_hour_str:
            if char.isalpha():
                if day_str and hour_str:
                    day = days.get(day_str, "Unknown Day")
                    for hour in hour_str:
                        try:
                            slot = time_slots[day][int(hour)-1]
                            day_hour_list.append((day, slot))
                        except:
                            continue
                    day_str = ''
                    hour_str = ''
                day_str += char
            elif char.isdigit():
                hour_str += char
        if day_str and hour_str:
            day = days.get(day_str, "Unknown Day")
            for hour in hour_str:
                try:
                    slot = time_slots[day][int(hour)-1]
                    day_hour_list.append((day, slot))
                except:
                    continue
    return day_hour_list

# Define time slots globally (based on your data)
time_slots = {
    'Monday': ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00', '12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40'],
    'Tuesday': ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00', '12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40'],
    'Wednesday': ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00', '12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40'],
    'Thursday': ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00', '12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40'],
    'Friday': ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00']
}

def parse_uploaded_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype='pdf')
    num_pages = len(doc)
    doc.close()

    tables = read_pdf(uploaded_file, pages='all', multiple_tables=True)
    if not tables:
        st.error("No tables detected inside PDF!")
        return None

    # Start with the first table
    df = remove_header(tables[0])
    column_names = df.columns

    # Merge all tables
    for i in range(1, len(tables)):
        try:
            temp_df = tables[i]
            header_row = pd.DataFrame([temp_df.columns], columns=column_names)
            temp_df.columns = column_names
            temp_df_with_header = pd.concat([header_row, temp_df], ignore_index=True)
            df = pd.concat([df, temp_df_with_header], ignore_index=True)
        except:
            continue

    # Identify header columns
    headers = df.columns
    COM_COD, COURSE_NO, COURSE_TITLE, CREDIT, SEC, INSTRUCTOR, ROOM, DAYS_HOURS = "", "", "", "", "", "", "", ""
    for col in headers:
        lower_col = col.lower()
        if 'com' in lower_col:
            COM_COD = col
        elif 'no.' in lower_col:
            COURSE_NO = col
        elif 'title' in lower_col:
            COURSE_TITLE = col
        elif 'credit' in lower_col:
            CREDIT = col
        elif 'sec' in lower_col:
            SEC = col
        elif 'instructor' in lower_col:
            INSTRUCTOR = col
        elif 'room' in lower_col:
            ROOM = col
        elif 'days' in lower_col:
            DAYS_HOURS = col

    # Save important header names
    st.session_state.COURSE_TITLE = COURSE_TITLE
    st.session_state.COURSE_NO = COURSE_NO
    st.session_state.CREDIT = CREDIT
    st.session_state.SEC = SEC
    st.session_state.INSTRUCTOR = INSTRUCTOR
    st.session_state.ROOM = ROOM
    st.session_state.DAYS_HOURS = DAYS_HOURS

    # Drop unnecessary columns
    if COM_COD in df.columns:
        df = df.drop(COM_COD, axis=1)

    # Fill missing values in important columns
    df = forward_fill_course_details(df, COURSE_NO, COURSE_TITLE, CREDIT)

    # Remove rows without Days/Hours
    df = df.dropna(subset=[DAYS_HOURS])

    # Create TIME SLOTS Column
    df['TIME SLOTS'] = df[DAYS_HOURS].apply(map_days_hours_to_time_slots)

    return df

def filter_df_by_target(df, selected_years, selected_disciplines):
    """
    Smarter filtering based on course code breakdown.
    """

    if df is None:
        return None

    year_prefix_map = {
        "First Year": '1',
        "Second Year": '2',
        "Third Year": '3',
        "Fourth Year": '4',
    }

    # Collect rows matching discipline and year
    filtered_rows = []

    for _, row in df.iterrows():
        course_code = row[st.session_state.COURSE_NO]

        try:
            parts = course_code.split(' ')
            discipline = parts[0] if len(parts) > 0 else ""
            year_info = parts[1] if len(parts) > 1 else ""

            # Discipline Match
            discipline_match = (discipline in selected_disciplines)

            # Year Match
            year_match = False
            if year_info.startswith('F') and len(year_info) >= 2:
                course_year = year_info[1]  # get '1', '2', '3', '4'
                for year in selected_years:
                    if course_year == year_prefix_map[year]:
                        year_match = True
                        break

            # Allow universal courses (BITS, PHY, BIO) if year matches
            if discipline not in ["CS", "BIOT", "EEE", "ECE", "CHE", "CE", "ME"]:
                discipline_match = True

            if discipline_match and year_match:
                filtered_rows.append(row)

        except Exception as e:
            continue

    filtered_df = pd.DataFrame(filtered_rows)

    return filtered_df.reset_index(drop=True)

def build_slot_counter_and_details(df):
    """
    Build two matrices:
    - Number of classes per slot
    - List of class names per slot
    """
    days_list = list(time_slots.keys())
    slots_list = ['7:30-8:20', '8:25-9:15', '9:20-10:10', '10:15-11:05', '11:10-12:00',
                  '12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40']

    counter_matrix = pd.DataFrame(0, index=slots_list, columns=days_list)
    details_matrix = pd.DataFrame("", index=slots_list, columns=days_list)

    for _, row in df.iterrows():
        course = row[st.session_state.COURSE_TITLE]
        section = row[st.session_state.SEC]
        if isinstance(row['TIME SLOTS'], list):
            for day, time_range in row['TIME SLOTS']:
                # 🚨 Ignore Friday afternoon slots
                if day == "Friday" and time_range in ['12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40']:
                    continue  

                try:
                    # Update counter
                    counter_matrix.at[time_range, day] += 1

                    # Update details
                    existing = details_matrix.at[time_range, day]
                    new_entry = f"{course} (Sec {section})"
                    if existing:
                        details_matrix.at[time_range, day] = existing + "; " + new_entry
                    else:
                        details_matrix.at[time_range, day] = new_entry

                except Exception as e:
                    continue

    return counter_matrix, details_matrix

def visualise_slot_counter(counter_matrix):
    st.subheader("📋 Class Load Timetable")
    st.dataframe(counter_matrix.style.highlight_max(axis=0, color='lightcoral'), use_container_width=True)

    st.subheader("🔥 Heatmap of Class Clashes")

    slots_list = list(counter_matrix.index)
    slot_labels = [f"Slot {i+1}: {slot}" for i, slot in enumerate(slots_list)]

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.heatmap(counter_matrix, annot=True, cmap="YlOrRd", fmt="d",
                linewidths=0.5, linecolor='gray', cbar_kws={"label": "Number of Classes"},
                yticklabels=slot_labels)  

    plt.yticks(rotation=0)  
    plt.title("Class Load Across Timetable Slots", fontsize=16)
    st.pyplot(fig)

def suggest_free_slots(counter_matrix):
    st.subheader("🎯 Best Slots for Events (Least Busy)")

    min_value = None
    best_slots = []

    # Step 1: Find the real minimum value considering Friday rule
    for day in counter_matrix.columns:
        for time_slot in counter_matrix.index:
            if day == "Friday" and time_slot in ['12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40']:
                continue  # skip dead Friday afternoon slots
            value = counter_matrix.at[time_slot, day]
            if (min_value is None) or (value < min_value):
                min_value = value

    # Step 2: Now find all slots matching that minimum value
    for day in counter_matrix.columns:
        for time_slot in counter_matrix.index:
            if day == "Friday" and time_slot in ['12:05-12:55', '1:00-1:50', '1:55-2:45', '2:50-3:40']:
                continue
            if counter_matrix.at[time_slot, day] == min_value:
                best_slots.append((day, time_slot))

    # Step 3: Display results
    if best_slots:
        st.success(f"Minimum Classes happening = {min_value}")

        for day, time_slot in best_slots:
            st.write(f"✅ **{day}** at **{time_slot}** is a great candidate for events!")
    else:
        st.warning("No suitable slots found!")

# Page Setup
st.set_page_config(layout="wide", page_title="Free Hours Analyzer", page_icon="📚")
st.image(image, use_container_width=True)
st.caption("Plan your events better by finding free hours across courses!")

# Form Input
with st.form("academic_info_form"):
    st.subheader("Step 1: Enter Academic Information")

    year_options = ["First Year", "Second Year", "Third Year", "Fourth Year"]
    semester_options = ["First Semester", "Second Semester"]
    discipline_options = ["CS", "BIOT", "EEE", "ECE", "CHE", "CE", "ME"]

    target_years = st.multiselect("Select Target Years:", options=year_options)
    current_semester = st.radio("Select Current Semester:", options=semester_options, horizontal=True)
    target_disciplines = st.multiselect(
        "Select Target Disciplines (leave empty for all disciplines):",
        options=discipline_options
        )

    uploaded_file = st.file_uploader("Upload the Academic Calendar PDF", type=["pdf"])

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    submitted = col2.form_submit_button("Find Free Hours")
    refresh = col4.form_submit_button("Refresh Session")

if refresh:
    st.experimental_rerun()
    
if submitted:
    if uploaded_file is not None:
        df = parse_uploaded_pdf(uploaded_file)

        if df is not None:
            filtered_df = filter_df_by_target(df, target_years, target_disciplines)
            counter_matrix, details_matrix = build_slot_counter_and_details(filtered_df)
            
            visualise_slot_counter(counter_matrix)
            suggest_free_slots(counter_matrix)

            # 🎯 NEW: Show Details Matrix
            st.subheader("📋 Detailed Timetable: Course and Section Info")
            st.dataframe(details_matrix, use_container_width=True)

    else:
        st.warning("Please upload a timetable PDF first.")


st.markdown(footer,unsafe_allow_html=True)
