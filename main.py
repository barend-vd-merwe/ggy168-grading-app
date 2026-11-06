import streamlit as st


home_page = st.Page(
    "pages/home.py",
    title = "Dashboard",
    default = True
)

prac_1 = st.Page(
    "pages/practical-assignment-1.py",
    title = "Practical Assignment 1 — Coordinate Conversion"
)

prac_2 = st.Page(
    "pages/practical-assignment-2.py",
    title = "Practical Assignment 2 — Working with Coordinates"
)

prac_3 = st.Page(
    "pages/practical-assignment-3.py",
    title = "Practical Assignment 3 — Direction"
)

prac_4 = st.Page(
    "pages/practical-assignment-4.py",
    title = "Practical Assignment 4 — Distance"
)

prac_5 = st.Page(
    "pages/practical-assignment-5.py",
    title = "Practical Assignment 5 — Area"
)

pages = st.navigation({
    "Home"       : [home_page],
    "Practicals" : [prac_1, prac_2, prac_3, prac_4, prac_5]
})

st.set_page_config(page_title="GGY 168 Grading App", layout="wide")
pages.run()
