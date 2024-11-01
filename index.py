import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Set page configuration (must be the first command in the script)
st.set_page_config(page_title="Study Plan & Timetable Generator", layout="centered")

# Database connection details
db_config = {
    'user': 'root',
    'password': 'spurtHi%4029%21%21',  # Replace with your actual MySQL password
    'host': 'localhost',
    'database': 'student_performance_db',
    'port': 3306  # Adjust if your MySQL server uses a different port
}

# Create a connection to the MySQL database
try:
    engine = create_engine(
        f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    st.success("Connected to the database successfully.")
except SQLAlchemyError as e:
    st.error(f"Failed to connect to the database: {str(e)}")

# Function to fetch student data based on ID
def fetch_student_data(student_id):
    try:
        query = "SELECT * FROM student_performance WHERE student_id = %s"
        df = pd.read_sql(query, con=engine, params=(student_id,))
        if df.empty:
            st.warning("No student found with this ID.")
        return df
    except SQLAlchemyError as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

# Function to insert new student data
def insert_student_data(student_data):
    try:
        student_data.to_sql('student_performance', con=engine, if_exists='append', index=False)
        st.success("Student data saved successfully!")
    except SQLAlchemyError as e:
        st.error(f"Error saving data: {str(e)}")

# Function to generate a daily study timetable
def generate_daily_timetable(subjects, subject_marks, available_study_hours):
    # Calculate subject study hours based on marks (lower marks = more hours)
    total_weight = sum(100 - mark for mark in subject_marks.values())
    subject_hours = {
        subject: round((100 - subject_marks[subject]) / total_weight * available_study_hours, 2)
        for subject in subjects
    }

    # Define study days and time slots
    study_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    time_slots = ["9:00 AM - 11:00 AM", "11:00 AM - 1:00 PM", "2:00 PM - 4:00 PM", "4:00 PM - 6:00 PM"]

    # Create an empty DataFrame to hold the timetable
    timetable = pd.DataFrame(index=study_days, columns=time_slots)

    # Distribute study hours across days and time slots
    for subject, hours in subject_hours.items():
        remaining_hours = hours
        for day in study_days:
            for slot in time_slots:
                if remaining_hours > 0:
                    allocated_hours = min(2, remaining_hours)
                    current_schedule = timetable.at[day, slot]

                    # Append the subject with allocated hours
                    if pd.isna(current_schedule):
                        timetable.at[day, slot] = f"{subject} ({allocated_hours} hr)"
                    else:
                        timetable.at[day, slot] += f", {subject} ({allocated_hours} hr)"

                    remaining_hours -= allocated_hours
    return timetable


# Function to generate the timetable in table format and display it
def generate(subjects_input, marks_input, available_study_hours):
    subjects = [subject.strip() for subject in subjects_input.split(",") if subject.strip()]
    marks = [float(mark.strip()) for mark in marks_input.split(",") if mark.strip()]

    # Check if subjects and marks have the same length
    if len(subjects) != len(marks):
        st.warning("The number of subjects and marks should be the same.")
    else:
        # Create a dictionary with subjects and marks
        subject_marks = dict(zip(subjects, marks))

        # Generate the timetable as a DataFrame
        daily_timetable = generate_daily_timetable(subjects, subject_marks, available_study_hours)

        # Display the timetable in table format
        st.write("Generated Weekly Study Timetable:")
        st.dataframe(daily_timetable)


# Streamlit app layout
st.title("Student Study Plan and Timetable Generator")

# Input form to add or search for students
option = st.radio(
    "Choose an action",
    ['Add Student Data', 'Fetch Student Study Plan and Generate Timetable'],
    key="action_option"
)

if option == 'Add Student Data':
    with st.form("student_form"):
        student_id = st.number_input("Student ID", min_value=1, key="student_id")
        attendance_percentage = st.number_input("Attendance Percentage", min_value=0.0, max_value=100.0, key="attendance_percentage")
        assignment_score = st.number_input("Assignment Score", min_value=0.0, max_value=10.0, key="assignment_score")
        mid_term_score = st.number_input("Mid-Term Score", min_value=0.0, max_value=100.0, key="mid_term_score")
        study_hours = st.number_input("Study Hours", min_value=0.0, max_value=24.0, key="study_hours")
        quiz_score = st.number_input("Quiz Score", min_value=0.0, max_value=10.0, key="quiz_score")
        final_exam_score = st.number_input("Final Exam Score", min_value=0.0, max_value=100.0, key="final_exam_score")

        submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        new_student = pd.DataFrame({
            'student_id': [student_id],
            'attendance_percentage': [attendance_percentage],
            'assignment_score': [assignment_score],
            'mid_term_score': [mid_term_score],
            'study_hours': [study_hours],
            'quiz_score': [quiz_score],
            'final_exam_score': [final_exam_score]
        })
        insert_student_data(new_student)

if option == 'Fetch Student Study Plan and Generate Timetable':
    student_id = st.number_input("Enter Student ID to fetch", min_value=1)
    #fetch_button = st.button("Fetch Plan and Generate Timetable")
    #if fetch_button():
    with st.container():
        with st.form("timetable form"):
            student_data = fetch_student_data(student_id)
            if not student_data.empty:
                st.write("Student Data:")
                st.dataframe(student_data)

                # Direct inputs
                subjects_input = st.text_input("Enter subjects separated by commas (e.g., Math, Physics, Chemistry)")
                marks_input = st.text_input("Enter corresponding subject marks separated by commas (e.g., 75, 60, 90)")
                available_study_hours = st.number_input("Enter Total Available Study Hours for the Week",min_value=0.0, max_value=168.0)

                submit = st.form_submit_button("Generate Timetable")
                if submit:
                    generate(subjects_input,marks_input,available_study_hours)
                    
