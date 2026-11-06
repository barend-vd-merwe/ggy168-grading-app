import streamlit as st
import cv2 as cv
import pandas as pd
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import io
from io import BytesIO
from streamlit_image_zoom import image_zoom
import base64
from datetime import datetime

# custom functions
# ------------------------------------------------------------
def prac_viewer(img_url, height=700, max_zoom_ratio=4.0, key="osd_viewer"):
    if isinstance(img, Image.Image):
        pil_img = img
    else:
        pil_img = Image.open(img)

    buffered = BytesIO()
    if pil_img.mode in ("RGB", "P"):
        pil_img = pil_img.convert("RGB")

    pil_img.save(buffered, format="JPEG", quality=95)
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    # openseadragon
    html_osd = f"""
    <!DOCTYPE html>
    <html style="height:100%">
    <head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/openseadragon.min.js"></script>
    <style>
    *, *:before, *:after {{
    box-sizing: border-box;
    }}
    
    body {{
    margin: 0;
    padding: 0;
    background-color: #F5F5DC;
    height: 100%;
    width: 100%;
    overflow: hidden;
    }}
    
    #openseadragon-container {{
    width: 100%;
    height: 100%;
    background-color: #F8F9FA;
    border: 10px solid #1C252C;
    border-radius: 8px;
    }}
    </style>
    </head>

    <body>
    <div id="openseadragon-container"></div>
    <script type="text/javascript">

    var viewer = OpenSeadragon({{
    id: "openseadragon-container",
    prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/",
    tileSources: {{
    type: 'image',
    url:  '{img_url}'
    }},
    
    defaultZoomLevel: 0,
    minZoomImageRatio: 0.1,
    maxZoomPixelRatio: {max_zoom_ratio},
    visibilityRatio: 1.0,
    constrainDuringPan: true,
    homeFillsViewer: false,

    showNavigationControl: true,
    navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,
    showRotationControl: false,
    showFullPageControl: true,
    showHomeControl: true,

    animationTime: 0.3,
    blendTime: 0.1,
    springStiffness: 10}});
    </script>
    </body>
    </html>
    """
    st.components.v1.html(html_osd, height=height, scrolling=False)

def grade_submission():
    q1_memo = pd.read_csv("prac-2-q1-memo.csv")
    q1_ans = {
        "q"            : ["a","b","c","d"],
        "lat_sub"      : [st.session_state["q1_a_lat"],
                          st.session_state["q1_b_lat"],
                          st.session_state["q1_c_lat"],
                          st.session_state["q1_d_lat"]],
        "lat_sub_card" : [st.session_state["q1_a_lat_card"],
                          st.session_state["q1_b_lat_card"],
                          st.session_state["q1_c_lat_card"],
                          st.session_state["q1_d_lat_card"]],
        "lon_sub"      : [st.session_state["q1_a_lon"],
                          st.session_state["q1_b_lon"],
                          st.session_state["q1_c_lon"],
                          st.session_state["q1_d_lon"]],
        "lon_sub_card" : [st.session_state["q1_a_lon_card"],
                          st.session_state["q1_b_lon_card"],
                          st.session_state["q1_c_lon_card"],
                          st.session_state["q1_d_lon_card"]]
    }

    q1_ans = pd.DataFrame(q1_ans)
    q1 = pd.merge(q1_memo, q1_ans, on = "q", how = "inner")
    q1[["lat_ans_deg", "lat_ans_min", "lat_ans_sec"]] = q1["lat_sub"].str.split("/", expand = True).astype(float)
    q1[["lon_ans_deg", "lon_ans_min", "lon_ans_sec"]] = q1["lon_sub"].str.split("/", expand = True).astype(float)

    q1_lat_deg_mod = (q1["lat_ans_deg"] == q1["lat_deg"]).astype(float)
    q1_lon_deg_mod = (q1["lon_ans_deg"] == q1["lon_deg"]).astype(float)
    q1_lat_min_mod = (q1["lat_ans_min"] == q1["lat_min"]).astype(float)
    q1_lon_min_mod = (q1["lon_ans_min"] == q1["lon_min"]).astype(float)

    q1_lat_fc = q1["lat_ans_sec"].between(q1["lat_sec"] - q1["fc"], q1["lat_sec"] + q1["fc"])
    q1_lat_pc = q1["lat_ans_sec"].between(q1["lat_sec"] - q1["pc"], q1["lat_sec"] + q1["pc"])
    q1_lat_opt = [q1_lat_fc, q1_lat_pc]
    q1_lat_grd = [1.0, 0.0]
    q1["grade"] += np.select(q1_lat_opt, q1_lat_grd, default = 0.0) * q1_lat_deg_mod * q1_lat_min_mod

    q1_lat_card_fc = (q1["lat_sub_card"] == q1["lat_card"]).astype(float)
    q1["grade"] += q1_lat_card_fc

    q1_lon_fc = q1["lon_ans_sec"].between(q1["lon_sec"] - q1["fc"], q1["lon_sec"] + q1["fc"])
    q1_lon_pc = q1["lon_ans_sec"].between(q1["lon_sec"] - q1["pc"], q1["lon_sec"] + q1["pc"])
    q1_lon_opt = [q1_lon_fc, q1_lon_pc]
    q1_lon_grd = [1.0, 0.0]
    q1["grade"] += np.select(q1_lon_opt, q1_lon_grd, default = 0.0) * q1_lon_deg_mod * q1_lon_min_mod

    q1_lon_card_fc = (q1["lon_sub_card"] == q1["lon_card"]).astype(float)
    q1["grade"] += q1_lon_card_fc

    st.session_state["q1a"] = q1.loc[q1["q"] == "a", "grade"].item()
    st.session_state["q1b"] = q1.loc[q1["q"] == "b", "grade"].item()
    st.session_state["q1c"] = q1.loc[q1["q"] == "c", "grade"].item()
    st.session_state["q1d"] = q1.loc[q1["q"] == "d", "grade"].item()
    st.session_state["q1_total"] = q1["grade"].sum()

    cv.putText(st.session_state["submission"], str(st.session_state["q1a"]),(2284,628),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q1b"]),(2284,859),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q1c"]),(2284,1090),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q1d"]),(2284,1315),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    q2 = {
        "q"       : ["a","b","c","d"],
        "credits" : [st.session_state["q2_a"],
                     st.session_state["q2_b"],
                     st.session_state["q2_c"],
                     st.session_state["q2_d"]],
        "grade"   : [0.0, 0.0, 0.0, 0.0]
    }

    q2 = pd.DataFrame(q2)
    q2_opt = [q2["credits"] == "Full Credit", q2["credits"] == "Partial Credit", q2["credits"] == "No Credit"]
    q2_grd = [2.0, 1.0, 0.0]
    q2["grade"] += np.select(q2_opt, q2_grd, default = 0.0)

    st.session_state["q2a"] = q2.loc[q2["q"] == "a", "grade"].item()
    st.session_state["q2b"] = q2.loc[q2["q"] == "b", "grade"].item()
    st.session_state["q2c"] = q2.loc[q2["q"] == "c", "grade"].item()
    st.session_state["q2d"] = q2.loc[q2["q"] == "d", "grade"].item()
    st.session_state["q2_total"] = q2["grade"].sum()

    cv.putText(st.session_state["submission"], str(st.session_state["q2a"]),(2284,1681),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q2b"]),(2284,1987),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q2c"]),(2284,2294),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q2d"]),(2284,2601),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["final_grade"] = st.session_state["q1_total"] + st.session_state["q2_total"]

    cv.putText(st.session_state["submission"], str(st.session_state["final_grade"]),(852,446),cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["student"]),(301,244),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = st.session_state["submission"]
    
def next_submission():
    st.session_state["script_index"] += 1
    st.session_state["q1_a_lat"] = ""
    st.session_state["q1_b_lat"] = ""
    st.session_state["q1_c_lat"] = ""
    st.session_state["q1_d_lat"] = ""
    st.session_state["q1_a_lat_card"] = None
    st.session_state["q1_b_lat_card"] = None
    st.session_state["q1_c_lat_card"] = None
    st.session_state["q1_d_lat_card"] = None
    st.session_state["q1_a_lon"] = ""
    st.session_state["q1_b_lon"] = ""
    st.session_state["q1_c_lon"] = ""
    st.session_state["q1_d_lon"] = ""
    st.session_state["q1_a_lon_card"] = None
    st.session_state["q1_b_lon_card"] = None
    st.session_state["q1_c_lon_card"] = None
    st.session_state["q1_d_lon_card"] = None
    st.session_state["q2_a"] = None
    st.session_state["q2_b"] = None
    st.session_state["q2_c"] = None
    st.session_state["q2_d"] = None
    
    
def clear_files():
    st.session_state["uploader_key"] += 1
    del st.session_state["script_index"]
    if "graded_submission" in st.session_state:
        del st.session_state["graded_submission"]

# ==============================
st.markdown(
    """
    <style>
    /* 1. Add Tuks Red border strip across the top of the app */
    header[data-testid="stHeader"] {
        border-top: 5px solid #D12631 !important;
    }

    /* 2. Style primary headers with UP Navy Blue */
    h1, h2, h3 {
        color: #002B49 !important;
    }

    /* 3. Style Sidebar header with a Gold bottom accent */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        border-bottom: 2px solid #E8A800;
        padding-bottom: 5px;
    }

    /* Custom utility classes */
    .tuks-red { color: #D12631; font-weight: bold; }
    .up-gold { color: #E8A800; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

st.set_page_config(layout="wide")

title_col1, title_col2= st.columns(2)
with title_col1:
    st.image("NAS_Faculty Logo.jpg")

with title_col2:
    st.title("GGY 168 — Introduction to Physical Geography")
    st.header("Practical Assignment 2 — Plotting")


with st.expander("Instructions", expanded = False):
    st.markdown("""
    ### Instructions
    1. Enter your name in the provided field.
    2. Load the student submission. It is now possible to load multiple submissions at the same time which should make the grading faster.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. For coordinates, the values should be separated by a forward slash. For example 56°24′65″ becomes 56/24/65.
    8. The cardinal direction only has two options: the correct answer and "Other". If the provided the wrong cardinal number, select "Other". If they did not provide a cardinal direction, select "Other'.
    9. For the plotting of points, if their mark is within the small red square select "Full Credit". If it is not within the small red square, but it is still inside the larger blue square, select "Partial Credit". If it is not within any of the two squares, select "No Credit". If it falls on one of the lines, assign the corresponding credit (for example if it falls on a red line assign full credit).
    10. When you are done, press the grade button.
    11. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
    12. If you uploaded multiplee submissions, press the next buttun.
    """)

if "script_index" not in st.session_state:
    st.session_state["script_index"] = 0

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# load class list and submission
with st.sidebar:
    grader = st.text_input("Name of grader", key="graderName")
    uploaded_files = st.file_uploader("Select the student submission",
                                      type = ["png"],
                                      accept_multiple_files = True,
                                      key = str(st.session_state["uploader_key"]))
    st.button("Clear", on_click = clear_files)

if uploaded_files and grader.strip():
    total_scripts = len(uploaded_files)
    current_script = st.session_state["script_index"] + 1
    progress = min(current_script / total_scripts, 1.0)
    st.progress(progress)

    # extract student details from img filename
    image = uploaded_files[st.session_state["script_index"]]
    filename = image.name
    filename = filename.replace(".png","")
    surname, name, emplid = filename.split("_")
    st.session_state["student"] = f"{name} {surname} ({emplid})"

    # read and display image
    img = Image.open(image)

    # store the submission in memory as cv2 object
    img_bytes = np.frombuffer(image.getvalue(), dtype=np.uint8)
    cv_img = cv.imdecode(img_bytes, cv.IMREAD_COLOR)

    # prepare values for detector
    aruco_dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
    parameters = cv.aruco.DetectorParameters()
    
    # instantiate detector
    detector = cv.aruco.ArucoDetector(aruco_dictionary, parameters)

    try:
        # use detector to detect aruco markers
        corners, ids, _ = detector.detectMarkers(cv_img)

        # get the coordinates of the points to maximise scanned area
        ids = ids.flatten().tolist()
        aruco_0_index = ids.index(0)
        aruco_0_corners = corners[aruco_0_index]
        aruco_0_corners = aruco_0_corners.squeeze()
        top_left = aruco_0_corners[0]

        aruco_1_index = ids.index(1)
        aruco_1_corners = corners[aruco_1_index]
        aruco_1_corners = aruco_1_corners.squeeze()
        top_right = aruco_1_corners[1]

        aruco_2_index = ids.index(2)
        aruco_2_corners = corners[aruco_2_index]
        aruco_2_corners = aruco_2_corners.squeeze()
        bottom_left = aruco_2_corners[3]

        aruco_3_index = ids.index(3)
        aruco_3_corners = corners[aruco_3_index]
        aruco_3_corners = aruco_3_corners.squeeze()
        bottom_right = aruco_3_corners[2]

        # Prepare the image for warping
        current_coords = np.float32([[top_left[0], top_left[1]],
                                     [top_right[0], top_right[1]],
                                     [bottom_right[0], bottom_right[1]],
                                     [bottom_left[0], bottom_left[1]]])
        target_coords = np.float32([[177,177],
                                    [2303,177],
                                    [2303,3330],
                                    [177,3330]])
        transformation_matrix = cv.getPerspectiveTransform(current_coords,
                                                           target_coords)

        # transform the image
        warped_img = cv.warpPerspective(cv_img,
                                        transformation_matrix,
                                        (2480,3508),
                                        borderMode=cv.BORDER_CONSTANT,
                                        borderValue=(255, 255, 255))

        # full credit squares
        fc = pd.read_csv("prac-2-plot-fc.csv")
        cv.rectangle(warped_img, (fc.iloc[0,3], fc.iloc[0,4]), (fc.iloc[1,3], fc.iloc[1,4]), (0,0,255), 2)
        cv.rectangle(warped_img, (fc.iloc[2,3], fc.iloc[2,4]), (fc.iloc[3,3], fc.iloc[3,4]), (0,0,255), 2)
        cv.rectangle(warped_img, (fc.iloc[4,3], fc.iloc[4,4]), (fc.iloc[5,3], fc.iloc[5,4]), (0,0,255), 2)
        cv.rectangle(warped_img, (fc.iloc[6,3], fc.iloc[6,4]), (fc.iloc[7,3], fc.iloc[7,4]), (0,0,255), 2)

        # patial credit regions
        pc = pd.read_csv("prac-2-plot-pc.csv")
        cv.rectangle(warped_img, (pc.iloc[0,3], pc.iloc[0,4]), (pc.iloc[1,3], pc.iloc[1,4]), (255,0,0), 2)
        cv.rectangle(warped_img, (pc.iloc[2,3], pc.iloc[2,4]), (pc.iloc[3,3], pc.iloc[3,4]), (255,0,0), 2)
        cv.rectangle(warped_img, (pc.iloc[4,3], pc.iloc[4,4]), (pc.iloc[5,3], pc.iloc[5,4]), (255,0,0), 2)
        cv.rectangle(warped_img, (pc.iloc[6,3], pc.iloc[6,4]), (pc.iloc[7,3], pc.iloc[7,4]), (255,0,0), 2)

        st.session_state["submission"] = warped_img

        processed_img = cv.imencode(".png",warped_img)[1]
        b64_str = base64.b64encode(processed_img).decode("utf-8")
        img_url = f"data:image/png;base64,{b64_str}"


    except Exception as e:
        st.error(f"Processing failed: {e}")
        img_url = None

    # display submission and grading tools in two cols
    col1, col2 = st.columns(2)

    with col1:    
        prac_viewer(img_url)

    with col2:
        # display student details
        with st.expander("Student Details", expanded = False):
            st.markdown(f"""
            - *Name*: **{name}**
            - *Surname*: **{surname}**
            - *Student Number*: **{emplid}**
            """)

        with st.expander("Question 1", expanded = False):
            q1_col1, q1_col2 = st.columns(2)

            with q1_col1:
                st.text_input("(a) Latitude", key = "q1_a_lat")
                st.text_input("(a) Longitude", key = "q1_a_lon")
                st.text_input("(b) Latitude", key = "q1_b_lat")
                st.text_input("(b) Longitude", key = "q1_b_lon")
                st.text_input("(c) Latitude", key = "q1_c_lat")
                st.text_input("(c) Longitude", key = "q1_c_lon")
                st.text_input("(d) Latitude", key = "q1_d_lat")
                st.text_input("(d) Longitude", key = "q1_d_lon")

            with q1_col2:
                st.selectbox("Direction",("S", "Other"), index = None, placeholder = "Make a selection...", key = "q1_a_lat_card")
                st.selectbox("Direction",("E", "Other"), index = None, placeholder = "Make a selection...", key = "q1_a_lon_card")
                st.selectbox("Direction",("S", "Other"), index = None, placeholder = "Make a selection...", key = "q1_b_lat_card")
                st.selectbox("Direction",("E", "Other"), index = None, placeholder = "Make a selection...", key = "q1_b_lon_card")
                st.selectbox("Direction",("S", "Other"), index = None, placeholder = "Make a selection...", key = "q1_c_lat_card")
                st.selectbox("Direction",("E", "Other"), index = None, placeholder = "Make a selection...", key = "q1_c_lon_card")
                st.selectbox("Direction",("S", "Other"), index = None, placeholder = "Make a selection...", key = "q1_d_lat_card")
                st.selectbox("Direction",("E", "Other"), index = None, placeholder = "Make a selection...", key = "q1_d_lon_card")

        with st.expander("Question 2", expanded = False):
            st.selectbox("Point P",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "q2_a")
            st.selectbox("Point Q",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "q2_b")
            st.selectbox("Point R",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "q2_c")
            st.selectbox("Point S",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "q2_d")

        button_col1, button_col2, button_col3 = st.columns(3)

        with button_col1:
            st.button("Grade", on_click = grade_submission)

        if "graded_submission" in st.session_state:
            final_img_rgb = cv.cvtColor(st.session_state["graded_submission"], cv.COLOR_BGR2RGB)
            final_img_pil = Image.fromarray(final_img_rgb)
            filename = filename + ".png"

            grader_timestamp = datetime.now().isoformat()
            meta_info = PngInfo()
            meta_info.add_text("Grader", grader.strip())
            meta_info.add_text("GradedAt", grader_timestamp)
            meta_info.add_text("final", str(st.session_state["final_grade"]))
            meta_info.add_text("q1", str(st.session_state["q1_total"]))
            meta_info.add_text("q2", str(st.session_state["q2_total"])) 
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
