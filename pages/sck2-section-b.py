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
import yaml
from streamlit_gsheets import GSheetsConnection
from pathlib import Path
import gc

BASE_DIR = Path(__file__).resolve().parent.parent

# custom functions
# ------------------------------------------------------------
def submission_viewer(img_url, height=1250, max_zoom_ratio=4.0, key="osd_viewer"):
    # openseadragon
    html_osd = f"""
    <!DOCTYPE html>
    <html style="height:100%">
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/openseadragon.min.js"></script>
        <style>
            body {{
    margin: 0;
    padding: 0;
    background-color: #F5F5DC;
    height: 100%;
    width: 100%;
    overflow: hidden;}}
            #openseadragon-container {{
                width: 100vw;
                height: 100vh;
                background: #F5F5DC;
                border: 10px solid #374151;
                border-radius: 8px;
    box-sizing: border-box;
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
                // Performance and Zoom configuration
                maxZoomPixelRatio: {max_zoom_ratio},
                minZoomImageRatio: 0.8,
                visibilityRatio: 0.8,
                constrainDuringPan: true,
                
                // Controls setup
                showNavigationControl: true,
                navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,
                showRotationControl: false,
                showFullPageControl: true,
                showHomeControl: true,
                
                // Smooth interaction tuning
                animationTime: 0.3,
                bllendTime: 0.1,
                springStiffness: 10
            }});
        </script>
    </body>
    </html>
    """
    st.iframe(html_osd, height=height)

# ------------------------------------------------------------
def dms_to_dd(dms):
    raw = dms.strip()
    parts = raw.split("/")
    nums = [float(p) for p in parts]
    if len(nums) != 3:
        st.error("Incorrect DMS entry. Entry must be dd/mm/ss (if there are no seconds, just enter 00).")
    else:
        try:
            deg, minutes, sec = [float(p) for p in parts]
            md = round(deg + (minutes / 60.0) + (sec / 3600.0), 4)
        except:
            st.error("Incorrect data entered.")
    return md

def grade_submission():
    with open (BASE_DIR / "tst2-memo.yaml", "r", encoding = "utf-8") as file:
        memo = yaml.safe_load(file)

    q9a_ans = memo["q9a"]["ans"]
    q9a_fc = memo["q9a"]["fc"]
    q9a_pc = memo["q9a"]["pc"]
    q9a_sub = float(st.session_state["q9a_val"])
    q9a_sub_units = st.session_state["q9a_unt"]
    q9a_grd = 0.0
    
    q9a_range = [
        (q9a_ans - q9a_fc, q9a_ans + q9a_fc, 0.5),
        (q9a_ans - q9a_pc, q9a_ans + q9a_pc, 0.25),
    ]

    q9a_grd += next((grade for lower, upper, grade in q9a_range if lower <= q9a_sub <= upper), 0)

    if q9a_sub_units == "fc":
        q9a_grd += 0.5
    else:
        q9a_grd += 0.0

    q9b_ans = memo["q9b"]["ans"]
    q9b_fc = memo["q9b"]["fc"]
    q9b_pc = memo["q9b"]["pc"]
    q9b_sub = float(st.session_state["q9b_val"])
    q9b_sub_units = st.session_state["q9b_unt"]
    q9b_grd = 0.0
    
    q9b_range = [
        (q9b_ans - q9b_fc, q9b_ans + q9b_fc, 0.5),
        (q9b_ans - q9b_pc, q9b_ans + q9b_pc, 0.25),
    ]

    q9b_grd += next((grade for lower, upper, grade in q9b_range if lower <= q9b_sub <= upper), 0)

    if q9b_sub_units == "fc":
        q9b_grd += 0.5
    else:
        q9b_grd += 0.0

    st.session_state["q9a_grd"] = q9a_grd
    st.session_state["q9b_grd"] = q9b_grd
    st.session_state["q9_grd"] = q9a_grd + q9b_grd

    # ============================================================
    q10_ans = memo["q10"]["ans"]
    q10_fc = memo["q10"]["fc"]
    q10_pc = memo["q10"]["pc"]
    q10_sub = st.session_state["q10_val"]
    q10_units = st.session_state["q10_unt"]
    q10_grd = 0.0

    if "/" in q10_sub:
        md = dms_to_dd(q10_sub)
    else:
        md = float(q10_sub.strip())

    q10_range = [
        (q10_ans - q10_fc, q10_ans + q10_fc, 2.0),
        (q10_ans - q10_pc, q10_ans + q10_pc, 1.0)
    ]

    q10_grd += next((grade for lower, upper, grade in q10_range if lower <= md <= upper),0)

    if q10_units == "West":
        q10_grd += 1.0
    else:
        q10_grd += 0.0

    st.session_state["q10_grd"] = q10_grd

    # ============================================================
    q11a_ans = memo["q11a"]["ans"]
    q11a_fc = memo["q11a"]["fc"]
    q11a_pc = memo["q11a"]["pc"]
    q11a_sub = st.session_state["q11a_val"]
    q11a_units = st.session_state["q11a_unt"]
    q11a_grd = 0.0

    if "/" in q11a_sub:
        mfb = dms_to_dd(q11a_sub)
    else:
        mfb = float(q11a_sub.strip())

    q11a_range = [
        (q11a_ans - q11a_fc, q11a_ans + q11a_fc, 1.0),
        (q11a_ans - q11a_pc, q11a_ans + q11a_pc, 1.0)
    ]

    q11a_grd += next((grade for lower, upper, grade in q11a_range if lower <= mfb <= upper),0)

    if q11a_units == "fc":
        q11a_grd += 1.0
    else:
        q11a_grd += 0.0

    st.session_state["q11a_grd"] = q11a_grd

    q11b_ans = memo["q11b"]["ans"]
    q11b_fc = memo["q11b"]["fc"]
    q11b_pc = memo["q11b"]["pc"]
    q11b_sub = st.session_state["q11b_val"]
    q11b_units = st.session_state["q11b_unt"]
    q11b_grd = 0.0

    if "/" in q11b_sub:
        mbb = dms_to_dd(q11b_sub)
    else:
        mbb = float(q11b_sub.strip())

    q11b_range = [
        (q11b_ans - q11b_fc, q11b_ans + q11b_fc, 1.0),
        (q11b_ans - q11b_pc, q11b_ans + q11b_pc, 1.0)
    ]

    q11b_grd += next((grade for lower, upper, grade in q11b_range if lower <= mbb <= upper),0)

    if q11b_units == "fc":
        q11b_grd += 1.0
    else:
        q11b_grd += 0.0

    st.session_state["q11b_grd"] = q11b_grd
    st.session_state["q11_grd"] = q11a_grd + q11b_grd

    # ============================================================
    q12_ans = memo["q12"]["ans"]
    q12_fc = memo["q12"]["fc"]
    q12_pc = memo["q12"]["pc"]
    q12_sub = st.session_state["q12_val"]
    q12_units = st.session_state["q12_unt"]
    q12_grd = 0.0

    if "/" in q12_sub:
        q12_tfb = dms_to_dd(q12_sub)
    else:
        q12_tfb = float(q12_sub.strip())

    q12_range = [
        (q12_ans - q12_fc, q12_ans + q12_fc, 2.0),
        (q12_ans - q12_pc, q12_ans + q12_pc, 1.0)
    ]

    q12_grd += next((grade for lower, upper, grade in q12_range if lower <= q12_tfb <= upper),0)

    if q12_units == "fc":
        q12_grd += 1.0
    else:
        q12_grd += 0.0

    st.session_state["q12_grd"] = q12_grd

    # ============================================================
    q13_ans = memo["q13"]["ans"]
    q13_fc = memo["q13"]["fc"]
    q13_pc = memo["q13"]["pc"]
    q13_sub = float(st.session_state["q13_val"])
    q13_units = st.session_state["q13_unt"]
    q13_grd = 0.0

    match q13_units:
        case "m":
            q13_sub = q13_sub * 1.0
            q13_grd += 1.0
        case "km":
            q13_sub = q13_sub * 1000.0
            q13_grd += 1.0
        case "mm":
            q13_sub = q13_sub / 1000.0
            q13_grd += 1.0
        case "nc":
            q13_grd += 0.0
    
    q13_range = [
        (q13_ans - q13_fc, q13_ans + q13_fc, 2.0),
        (q13_ans - q13_pc, q13_ans + q13_pc, 1.0)
    ]

    q13_grd += next((grade for lower, upper, grade in q13_range if lower <= q13_sub <= upper),0)

    st.session_state["q13_grd"] = q13_grd

    # ============================================================
    q14_ans = memo["q14"]["ans"]
    q14_fc = memo["q14"]["fc"]
    q14_pc = memo["q14"]["pc"]
    q14_sub = float(st.session_state["q14_val"])
    q14_units = st.session_state["q14_unt"]
    q14_work = st.session_state["q14_wrk"]
    q14_grd = 0.0

    match q14_units:
        case "m":
            q14_sub = q14_sub * 1.0
            q14_grd += 1.0
        case "km":
            q14_sub = q14_sub * 1000.0
            q14_grd += 1.0
        case "mm":
            q14_sub = q14_sub / 1000.0
            q14_grd += 1.0
    
    q14_range = [
        (q14_ans - q14_fc, q14_ans + q14_fc, 3.0),
        (q14_ans - q14_pc, q14_ans + q14_pc, 1.5)
    ]

    q14_grd += next((grade for lower, upper, grade in q14_range if lower <= q14_sub <= upper),0)

    if q14_units == "fc":
        q14_grd += 1.0
    else:
        q14_grd += 0.0

    st.session_state["q14_ans"] = q14_grd

    match q14_work:
        case "fc":
            q14_grd += 4.0
            st.session_state["q14_plot"] = 4.0
        case "pc":
            q14_grd += 2.0
            st.session_state["q14_plot"] = 2.0
        case "nc":
            q14_grd += 0.0
            st.session_state["q14_plot"] = 0.0

    st.session_state["q14_grd"] = q14_grd

    st.session_state["final_grade"] = sum([st.session_state["q9a_grd"],
                                           st.session_state["q9b_grd"],
                                           st.session_state["q10_grd"],
                                           st.session_state["q11a_grd"],
                                           st.session_state["q11b_grd"],
                                           st.session_state["q12_grd"],
                                           st.session_state["q13_grd"],
                                           st.session_state["q14_grd"]])

    conn = st.connection("gsheets", type=GSheetsConnection)
    gc = conn.read(ttl=0)
    column_name = "Semester test 2 Section B [Total Pts: 23 Score] |2953723"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade"]
    conn.update(data=gc)

    cv.putText(st.session_state["submission"], str(st.session_state["final_grade"]), (850,455), cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], st.session_state["student"], (303,199), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(st.session_state["submission"], str(st.session_state["q9a_grd"]),(2226,367), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q9b_grd"]),(2226,473), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q10_grd"]),(2226,573), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q11a_grd"]),(2226,667), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q11b_grd"]),(2226,767), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q12_grd"]),(2226,861), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q13_grd"]),(2226,961), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q14_ans"]),(2226,1055), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(st.session_state["submission"], str(st.session_state["q14_plot"]),(1863,2767), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = st.session_state["submission"]

def set_q9_blank():
    st.session_state["q9a_val"] = "0.0"
    st.session_state["q9b_val"] = "0.0"
    st.session_state["q9a_unt"] = "nc"
    st.session_state["q9b_unt"] = "nc"

def set_q10_blank():
    st.session_state["q10_val"] = "99/99/99"
    st.session_state["q10_unt"] = "Other"

def set_q11_blank():
    st.session_state["q11a_val"] = "0.0"
    st.session_state["q11b_val"] = "0.0"
    st.session_state["q11a_unt"] = "nc"
    st.session_state["q11b_unt"] = "nc"

def set_q12_blank():
    st.session_state["q12_val"] = "0.0"
    st.session_state["q12_unt"] = "nc"

def set_q13_blank():
    st.session_state["q13_val"] = "0.0"
    st.session_state["q13_unt"] = "nc"

def set_q14_blank():
    st.session_state["q14_val"] = "0.0"
    st.session_state["q14_unt"] = "nc"
    st.session_state["q14_wrk"] = "nc"
    
def next_submission():
    st.session_state["script_index"] += 1
    del st.session_state["graded_submission"]
    # ============================================================
    st.session_state["q9a_val"] = ""
    st.session_state["q9b_val"] = ""
    st.session_state["q9a_unt"] = None
    st.session_state["q9b_unt"] = None
    st.session_state["q10_val"] = ""
    st.session_state["q10_unt"] = None
    st.session_state["q11a_val"] = ""
    st.session_state["q11b_val"] = ""
    st.session_state["q11a_unt"] = None
    st.session_state["q11b_unt"] = None
    st.session_state["q12_val"] = ""
    st.session_state["q12_unt"] = None
    st.session_state["q13_val"] = ""
    st.session_state["q13_unt"] = None
    st.session_state["q14_val"] = ""
    st.session_state["q14_unt"] = None
    st.session_state["q14_direction"] = 0
    st.session_state["q14_wrk"] = None
    # ============================================================
    st.rerun()

def clear_files():
     st.session_state["uploader_key"] += 1
     del st.session_state["script_index"]
     if "graded_submission" in st.session_state:
         del st.session_state["graded_submission"]

# ============================================================
# ============================================================

st.set_page_config(layout="wide")

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

title_col1, title_col2= st.columns(2)
with title_col1:
    st.image(BASE_DIR / "NAS_Faculty Logo.jpg")

with title_col2:
    st.title("GGY 168 — Introduction to Physical Geography")
    st.header("Semester Test 2")
    st.subheader("Section B — Cartography")

with st.expander("Instructions", expanded = False):
    st.markdown("""
    1. Enter your name in the provided space.
    2. Load the student submission.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. For the work shown requirement for question 14:
        - "Full Credit": At least four (4) of the circles contain a compass interval.
        - "Partial Credit": Compass marks are present, but correspond with three (3) or less of the indicated circles.
        - "No Credit": Compass marks are absent.
    8. **DON'T** use commas for decimal marks. Please use a full-stop.
    9. When you are done, press the grade button.
    10. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
    """)

if "script_index" not in st.session_state:
    st.session_state["script_index"] = 0

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 100

# load class list and submission
with st.sidebar:
    grader = st.text_input("Name of grader", key="graderName")
    pin = st.text_input("Enter PIN number",
                        type = "password",
                        key = "user_pin")
    uploaded_files = st.file_uploader("Select the student submission",
                                      type = ["png"],
                                      accept_multiple_files = True,
                                      key = str(st.session_state["uploader_key"]))
    st.button("Clear", on_click = clear_files)

valid_pin = st.secrets.get("secret_pin")

if uploaded_files and grader.strip() and st.session_state["user_pin"].strip() == valid_pin:
    # display submission and grading tools in two cols
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Direction of measurement",
                     ("Mox to Kelt", "Kelt to Mox"),
                     index = 0,
                     key = "q14_direction")

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

        # store the submission in memory as cv2 object
        img_bytes = np.frombuffer(image.getvalue(), dtype=np.uint8)
        cv_img = cv.imdecode(img_bytes, cv.IMREAD_COLOR)

        # prepare values for detector
        aruco_dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
        parameters = cv.aruco.DetectorParameters()
        parameters.cornerRefinementMethod = cv.aruco.CORNER_REFINE_SUBPIX
        parameters.cornerRefinementWinSize = 5
        parameters.cornerRefinementMaxIterations = 100
        parameters.cornerRefinementMinAccuracy = 0.01

        # instantiate detector
        detector = cv.aruco.ArucoDetector(aruco_dictionary, parameters)

        try:
            # use detector to detect aruco markers
            corners, ids, _ = detector.detectMarkers(cv_img)

            # get the coordinates of the center points of each aruco marker
            ids = ids.flatten().tolist()

            aruco_0_index = ids.index(0)
            aruco_0_corners = corners[aruco_0_index]
            aruco_0_corners_rshp = aruco_0_corners.reshape((4,2))

            aruco_1_index = ids.index(1)
            aruco_1_corners = corners[aruco_1_index]
            aruco_1_corners_rshp = aruco_1_corners.reshape((4,2))

            aruco_2_index = ids.index(2)
            aruco_2_corners = corners[aruco_2_index]
            aruco_2_corners_rshp = aruco_2_corners.reshape((4,2))

            aruco_3_index = ids.index(3)
            aruco_3_corners = corners[aruco_3_index]
            aruco_3_corners_rshp = aruco_3_corners.reshape((4,2))

            aruco_markers = [aruco_0_corners_rshp,
                             aruco_1_corners_rshp,
                             aruco_2_corners_rshp,
                             aruco_3_corners_rshp]

            current_coords_list = []
            for marker in aruco_markers:
                for i in range(4):
                    x_coord = marker[i,0]
                    y_coord = marker[i,1]
                    current_coords_list.append([x_coord, y_coord])
            current_coords = np.array(current_coords_list, dtype=np.float32)

            # Set target coordinates

            ac = pd.read_csv(BASE_DIR / "aruco.csv")

            target_coords_list = []

            for i in range(len(ac)):
                x_coord = ac.iloc[i,4]
                y_coord = ac.iloc[i,5]
                target_coords_list.append([x_coord, y_coord])

            target_coords = np.array(target_coords_list, dtype=np.float32)

            # transform the image
            homography_matrix, mask = cv.findHomography(current_coords, target_coords, cv.RANSAC, 5.0)
            warped_img = cv.warpPerspective(cv_img,
                                            homography_matrix,
                                            (2480, 3508),
                                            flags=cv.INTER_LINEAR,
                                            borderMode=cv.BORDER_CONSTANT,
                                            borderValue=(255, 255, 255))
            # add compass intervals
            shift = 8
            factor = 1 << shift
            bubble_radius = int(round(24 * factor))

            if st.session_state["q14_direction"] == "Mox to Kelt":
                submission = warped_img.copy()
                del warped_img
                del cv_img
                gc.collect()
                ci = pd.read_csv(BASE_DIR / "mk-compass-intervals.csv")
                for i in range(len(ci)):
                    rawx = ci.iloc[i]["cvx"]
                    rawy = ci.iloc[i]["cvy"]
                    cix = int(round(rawx * factor))
                    ciy = int(round(rawy * factor))
                    cv.circle(submission, (cix, ciy), bubble_radius, (0,0,255), 2, shift = shift)
                    st.session_state["submission"] = submission
            else:
                submission = warped_img.copy()
                del warped_img
                del cv_img
                gc.collect()
                ci = pd.read_csv(BASE_DIR / "km-compass-intervals.csv")
                for i in range(len(ci)):
                    rawx = ci.iloc[i]["cvx"]
                    rawy = ci.iloc[i]["cvy"]
                    cix = int(round(rawx * factor))
                    ciy = int(round(rawy * factor))
                    cv.circle(submission, (cix, ciy), bubble_radius, (0,0,255), 2, shift = shift)
                    st.session_state["submission"] = submission
            
            _, disp_img = cv.imencode(".jpg",submission, [int(cv.IMWRITE_JPEG_QUALITY), 80])
            b64_str = base64.b64encode(disp_img).decode("utf-8")
            img_url = f"data:image/png;base64,{b64_str}"


        except Exception as e:
            st.error(f"Processing failed: {e}")
            img_url = None
  
        submission_viewer(img_url)

    with col2:
        # display student details
        with st.expander("Student Details", expanded = False):
            st.markdown(f"""
            - *Name*: **{name}**
            - *Surname*: **{surname}**
            - *Student Number*: **{emplid}**
            """)

        with st.expander("Questions", expanded = True):
            st.markdown("**Question 9**")
            st.button("Blank",
                      on_click=set_q9_blank,
                      key = "q9_blank")
            q9_col1, q9_col2 = st.columns(2)
            
            with q9_col1:
                st.text_input("Tfb (Bryn to Mox)", key = "q9a_val")
                st.text_input("Tbb (Bryn to Mox)", key = "q9b_val")

            with q9_col2:
                st.selectbox("Units",
                             ("fc", "nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q9a_unt")
                st.selectbox("Units",
                             ("fc", "nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q9b_unt")
            
                
            st.markdown("**Question 10**")
            st.button("Blank",
                      on_click=set_q10_blank,
                      key = "q10_blank")
            q10_col1, q10_col2 = st.columns(2)

            with q10_col1:
                st.text_input("Magnetic Declination", key = "q10_val")

            with q10_col2:
                st.selectbox("Units",
                             ("West", "Other"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q10_unt")

            st.markdown("**Question 11**")
            st.button("Blank",
                      on_click=set_q11_blank,
                      key = "q11_blank")
            q11_col1, q11_col2 = st.columns(2)

            with q11_col1:
                st.text_input("Mfb (Kelt to Zuni)", key = "q11a_val")
                st.text_input("Mbb (Kelt to Zuni)", key = "q11b_val")

            with q11_col2:
                st.selectbox("Units",
                             ("fc", "nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q11a_unt")
                st.selectbox("Units",
                             ("fc", "nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q11b_unt")

            st.markdown("**Question 12**")
            st.button("Blank",
                      on_click=set_q12_blank,
                      key = "q12_blank")
            q12_col1, q12_col2 = st.columns(2)

            with q12_col1:
                st.text_input("True Forward Bearing", key = "q12_val")

            with q12_col2:
                st.selectbox("Units",
                             ("fc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q12_unt")

            st.markdown("**Question 13**")
            st.button("Blank",
                      on_click=set_q13_blank,
                      key = "q13_blank")
            q13_col1, q13_col2 = st.columns(2)

            with q13_col1:
                st.text_input("Straight line distance", key = "q13_val")

            with q13_col2:
                st.selectbox("Units",
                             ("m","km","mm","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q13_unt")

            st.markdown("**Question 14**")
            st.button("Blank",
                      on_click=set_q14_blank,
                      key = "q14_blank")
            q14_col1, q14_col2, q14_col3 = st.columns(3)

            with q14_col1:
                st.text_input("Road length", key = "q14_val")

            with q14_col2:
                st.selectbox("Units",
                             ("m","km","mm","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q14_unt")

            with q14_col3:
                st.selectbox("Work shown",
                             ("fc","pc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q14_wrk")
            

        button_col1, button_col2, button_col3 = st.columns(3)

        with button_col1:
            st.button("Grade", on_click=grade_submission)

        if "graded_submission" in st.session_state:
            final_img_rgb = cv.cvtColor(st.session_state["graded_submission"], cv.COLOR_BGR2RGB)
            final_img_pil = Image.fromarray(final_img_rgb)

            filename = filename + ".png"
            grader_timestamp = datetime.now().isoformat()
            meta_info = PngInfo()
            meta_info.add_text("Grader", grader.strip())
            meta_info.add_text("GradedAt", grader_timestamp)
            meta_info.add_text("final", str(st.session_state["final_grade"]))
            meta_info.add_text("q9", str(st.session_state["q9_grd"]))
            meta_info.add_text("q10", str(st.session_state["q10_grd"]))  
            meta_info.add_text("q11", str(st.session_state["q11_grd"]))  
            meta_info.add_text("q12", str(st.session_state["q12_grd"]))  
            meta_info.add_text("q13", str(st.session_state["q13_grd"]))  
            meta_info.add_text("q14", str(st.session_state["q14_grd"]))
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
