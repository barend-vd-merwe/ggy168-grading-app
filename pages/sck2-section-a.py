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

BASE_DIR = Path(__file__).resolve().parent.parent

# custom functions
# ------------------------------------------------------------
def submission_viewer(img_url, height=1000, max_zoom_ratio=4.0, key="osd_viewer"):
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
def grade_submission():
    with open (BASE_DIR / "tst2-memo.yaml", "r", encoding = "utf-8") as file:
        memo = yaml.safe_load(file)

    q1a_grade = 0.0
    q1b_grade = 0.0
    q1c_grade = 0.0

    q1a_ans = memo["q1a"]["ans"]
    q1a_fc = memo["q1a"]["fc"]
    q1a_pc = memo["q1a"]["pc"]
    q1a_sub = float(st.session_state["q1a_sub"])

    q1a_range = [
        (q1a_ans - q1a_fc, q1a_ans + q1a_fc, 1.0),
        (q1a_ans - q1a_pc, q1a_ans + q1a_pc, 0.5)
    ]

    q1a_grade += next((grade for lower, upper, grade in q1a_range if lower <= q1a_sub <= upper), 0)

    q1_unit_sub = st.session_state["q1a_unit"]
    
    match q1_unit_sub:
        case "fc":
            q1a_grade += 1.0
        case "pc":
            q1a_grade += 0.5
        case "nc":
            q1a_grade += 0.0
            
    q1b_sub = st.session_state["q1b_weathering"]
    q1b_ans = memo["q1b"]["ans"]

    if q1b_sub == q1b_ans:
        q1b_grade += 2.0

    q1c_sub = st.session_state["q1c_motivation"]

    match q1c_sub:
        case "fc":
            q1c_grade += 4.0
        case "pc":
            q1c_grade += 2.0
        case "nc":
            q1c_grade += 0.0

    st.session_state["q1_grade"] = q1a_grade + q1b_grade + q1c_grade

    # ============================================================
    q2a_ans = memo["q2a"]["ans"]
    q2b_ans = memo["q2b"]["ans"]

    q2a_grade = 0.0
    q2b_grade = 0.0

    q2a_sub = st.session_state["q2a"]
    q2b_sub = st.session_state["q2b"]

    if q2a_sub == q2a_ans:
        q2a_grade += 0.5

    if q2b_sub == q2b_ans:
        q2b_grade += 0.5

    st.session_state["q2_grade"] = q2a_grade + q2b_grade

    # ============================================================

    q3_ans = memo["q3"]["ans"]
    q3_fc = memo["q3"]["fc"]
    q3_pc = memo["q3"]["pc"]

    q3_sub = float(st.session_state["q3_sub"])

    q3_grade = 0.0

    q3_range = [
        (q3_ans - q3_fc, q3_ans + q3_fc, 2.0),
        (q3_ans - q3_pc, q3_ans + q3_pc, 1.0)
    ]

    q3_grade += next((grade for lower, upper, grade in q3_range if lower <= q3_sub <= upper), 0)
    st.session_state["q3_grade"] = q3_grade
    # ============================================================
    q4_ans = memo["q4"]["ans"]
    q4_sub = st.session_state["q4_shape"]
    q4_work = st.session_state["q4_wrk"]
    q4_grade = 0.0

    if q4_sub == q4_ans:
        q4_grade += 1.0
    else:
        q4_grade += 0.0

    match q4_work:
        case "fc":
            q4_grade += 1.0
        case "pc":
            q4_grade += 0.5
        case "nc":
            q4_grade += 0.0

    st.session_state["q4_grade"] = q4_grade

    # ============================================================
    q5a_ans = memo["q5a"]["ans"]
    q5a_sub = st.session_state["q5a"]
    q5a_grade = 0.0
    q5b_grade = 0.0

    if q5a_sub == q5a_ans:
        q5a_grade += 1.0
    else:
        q5a_grade += 0.0

    q5b_mot = st.session_state["q5b"]

    match q5b_mot:
        case "fc":
            q5b_grade += 2.0
        case "pc":
            q5b_grade += 1.0
        case "nc":
            q5b_grade += 0.0

    st.session_state["q5_grade"] = q5a_grade + q5b_grade
    
    # ============================================================
    q6a_ans = memo["q6a"]["ans"]
    q6b_ans = memo["q6b"]["ans"]
    q6c_ans = memo["q6c"]["ans"]
    q6a_sub = st.session_state["q6a"]
    q6b_sub = st.session_state["q6b"]
    q6c_sub = st.session_state["q6c"]
    q6a_grade = 0.0
    q6b_grade = 0.0
    q6c_grade = 0.0

    if q6a_sub == q6a_ans:
        q6a_grade += 3.0
    else:
        q6a_grade += 0.0

    if q6b_sub == q6b_ans:
        q6b_grade += 1.0
    else:
        q6b_grade += 0.0

    if q6c_sub == q6c_ans:
        q6c_grade += 1.0
    else:
        q6c_grade += 0.0

    st.session_state["q6_grade"] = q6a_grade + q6b_grade + q6c_grade
    
    # ============================================================
    q7a_ans = memo["q7a"]["ans"]
    q7a_fc = memo["q7a"]["fc"]
    q7a_pc = memo["q7a"]["pc"]
    q7a_sub = float(st.session_state["q7a"])
    q7a_units = st.session_state["q7a_unt"]


    q7a_grade = 0.0
    q7a_range = [
        (q7a_ans - q7a_fc, q7a_ans + q7a_fc, 0.5),
        (q7a_ans - q7a_pc, q7a_ans + q7a_pc, 0.25)
    ]
    
    q7a_grade += next((grade for lower, upper, grade in q7a_range if lower <= q7a_sub <= upper), 0)

    match q7a_units:
        case "fc":
            q7a_grade += 0.5
        case "nc":
            q7a_grade += 0.0

    q7b_ans = memo["q7b"]["ans"]
    q7b_sub = st.session_state["q7b"]
    q7b_grade = 0.0

    if q7b_sub == q7b_ans:
        q7b_grade += 1.0
    else:
        q7b_grade += 0.0

    q7c_sub = st.session_state["q7c"]
    q7c_grade = 0.0

    match q7c_sub:
        case "fc":
            q7c_grade += 3.0
        case "pc":
            q7c_grade += 1.5
        case "nc":
            q7c_grade += 0.0

    st.session_state["q7_grade"] = q7a_grade + q7b_grade + q7c_grade

    # ============================================================
    q8a_ans = memo["q8a"]["ans"]
    q8b_ans = memo["q8b"]["ans"]
    q8c_ans = memo["q8c"]["ans"]

    q8a_sub = float(st.session_state["q8a"])
    q8b_sub = float(st.session_state["q8b"])
    q8c_sub = float(st.session_state["q8c"])

    q8a_units = st.session_state["q8a_unt"]
    q8b_units = st.session_state["q8b_unt"]
    q8c_units = st.session_state["q8c_unt"]

    q8a_fc = memo["q8a"]["fc"]
    q8b_fc = memo["q8b"]["fc"]
    q8c_fc = memo["q8c"]["fc"]

    q8a_pc = memo["q8a"]["pc"]
    q8b_pc = memo["q8b"]["pc"]
    q8c_pc = memo["q8c"]["pc"]

    q8a_grade = 0.0
    q8b_grade = 0.0
    q8c_grade = 0.0

    q8a_range = [
        (q8a_ans - q8a_fc, q8a_ans + q8a_fc, 0.5),
        (q8a_ans - q8a_pc, q8a_ans + q8a_pc, 0.25)
    ]

    q8a_grade += next((grade for lower, upper, grade in q8a_range if lower <= q8a_sub <= upper), 0)

    match q8a_units:
        case "fc":
            q8a_grade += 0.5
        case "nc":
            q8a_grade += 0.0

    q8b_range = [
        (q8b_ans - q8b_fc, q8b_ans + q8b_fc, 0.5),
        (q8b_ans - q8b_pc, q8b_ans + q8b_pc, 0.25)
    ]

    q8b_grade += next((grade for lower, upper, grade in q8b_range if lower <= q8b_sub <= upper), 0)

    match q8b_units:
        case "fc":
            q8b_grade += 0.5
        case "nc":
            q8b_grade += 0.0

    q8c_range = [
        (q8c_ans - q8c_fc, q8c_ans + q8c_fc, 0.5),
        (q8c_ans - q8c_pc, q8c_ans + q8c_pc, 0.25)
    ]

    q8c_grade += next((grade for lower, upper, grade in q8c_range if lower <= q8c_sub <= upper), 0)

    match q8c_units:
        case "fc":
            q8c_grade += 0.5
        case "nc":
            q8c_grade += 0.0

    st.session_state["q8_grade"] = q8a_grade + q8b_grade + q8c_grade

    st.session_state["final_grade"] = sum([st.session_state["q1_grade"],
                                           st.session_state["q2_grade"],
                                           st.session_state["q3_grade"],
                                           st.session_state["q4_grade"],
                                           st.session_state["q5_grade"],
                                           st.session_state["q6_grade"],
                                           st.session_state["q7_grade"],
                                           st.session_state["q8_grade"]])

    conn = st.connection("gsheets", type=GSheetsConnection)
    spreadsheet_url = st.secrets.get("spreadsheet")
    gc = conn.read(spreadsheet = spreadsheet_url,
                   ttl=0)
    column_name = "Semester test 2 Section A [Total Pts: 29 Score] |2953721"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade"]
    conn.update(data=gc)

    cv.putText(warped_img, str(st.session_state["final_grade"]), (850,455), cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(warped_img, st.session_state["student"], (303,199), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q1a_grade),(2314,393), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q1b_grade),(2314,499), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q1c_grade),(2314,643), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q2a_grade),(1171,1332), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q2b_grade),(2227,1332), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q3_grade),(2314,1443), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q4_grade),(2314,1562), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q5a_grade),(2314,1668), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q5b_grade),(2314,1818), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q6a_grade),(2314,2324), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q6b_grade),(2314,2430), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q6c_grade),(2314,2530), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q7a_grade),(1170,2637), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q7b_grade),(2239,2637), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q7c_grade),(2314,2755), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(q8a_grade),(817,3146), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q8b_grade),(1542,3146), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(q8c_grade),(2248,3146), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = warped_img

def next_submission():
    st.session_state["script_index"] += 1
    del st.session_state["graded_submission"]
    # ==============================
    st.session_state["q1a_sub"] = ""
    st.session_state["q1a_unit"] = None
    st.session_state["q1a_weathering"] = None
    st.session_state["q1c_motivation"] = None
    st.session_state["q2a"] = None
    st.session_state["q2b"] = None
    st.session_state["q3_sub"] = ""
    st.session_state["q4_shape"] = None
    st.session_state["q4_wrk"] = None
    st.session_state["q5a"] = None
    st.session_state["q5b"] = None
    st.session_state["q6a"] = None
    st.session_state["q6b"] = None
    st.session_state["q6c"] = None
    st.session_state["q7a"] = ""
    st.session_state["q7a_unt"] = None
    st.session_state["q7b"] = None
    st.session_state["q7c"] = None
    st.session_state["q8a"] = ""
    st.session_state["q8a_unt"] = None
    st.session_state["q8b"] = ""
    st.session_state["q8b_unt"] = None
    st.session_state["q8c"] = ""
    st.session_state["q8c_unt"] = None
    
    
    st.rerun()

def clear_files():
     st.session_state["uploader_key"] += 1
     del st.session_state["script_index"]
     if "graded_submission" in st.session_state:
         del st.session_state["graded_submission"]
# ------------------------------------------------------------
    
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
    st.subheader("Section A — Theory")

with st.expander("Instructions", expanded = False):
    st.markdown("""
    1. Enter your name in the provided space.
    2. Load the student submission.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. **DON'T** use commas for decimal marks. Please use a full-stop.
    9. When you are done, press the grade button.
    10. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
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

    # store the submission in memory as cv2 object
    img_bytes = np.frombuffer(image.getvalue(), dtype=np.uint8)
    cv_img = cv.imdecode(img_bytes, cv.IMREAD_COLOR)
    img_gray = cv.cvtColor(cv_img, cv.COLOR_BGR2GRAY)

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
        corners, ids, _ = detector.detectMarkers(img_gray)

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
        # get zingg point
        shift = 8
        factor = 1 << shift
        zingg=pd.read_csv(BASE_DIR / "zingg.csv")
        tlx = int(round(zingg.iloc[0,3] * factor))
        tly = int(round(zingg.iloc[0,4] * factor))
        brx = int(round(zingg.iloc[1,3] * factor))
        bry = int(round(zingg.iloc[1,4] * factor))

        cv.rectangle(warped_img, (tlx,tly), (brx,bry), (0,0,255), thickness = 2, shift = shift)

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
        submission_viewer(img_url)

    with col2:
        # display student details
        with st.expander("Student Details", expanded = False):
            st.markdown(f"""
            - *Name*: **{name}**
            - *Surname*: **{surname}**
            - *Student Number*: **{emplid}**
            """)

        with st.expander("Questions 1 to 3", expanded = False):
            st.markdown("**Question 1**")
            q1_col1, q1_col2 = st.columns(2)

            with q1_col1:
                st.text_input("Change in Gibbs Free Energy", key = "q1a_sub")
                st.selectbox("Weathering Reaction", ("Yes", "No"), index = None, placeholder = "Make a selection..", key = "q1b_weathering")

            with q1_col2:
                st.selectbox("Units", ("fc","pc","nc"), index = None, placeholder="Make a selection...", key = "q1a_unit")
                st.selectbox("Motivation", ("fc","pc","nc"), index = None, placeholder = "Make a selection..", key = "q1c_motivation")

            st.markdown("**Question 2**")
            q2_col1, q2_col2 = st.columns(2)

            with q2_col1:
                st.selectbox("a) 0.002 mm", ("Clay", "Other"), index = None, placeholder = "Make a selection...", key = "q2a")

            with q2_col2:
                st.selectbox("a) 0.01 mm", ("Fine Silt", "Other"), index = None, placeholder = "Make a selection...", key = "q2b")

            st.markdown("**Question 3**")
            st.text_input("Phi size", key = "q3_sub")

        with st.expander("Questions 4 to 8", expanded = False):
            st.markdown("**Question 4**")
            q4_col1, q4_col2 = st.columns(2)

            with q4_col1:
                st.selectbox("Clast shape",
                             ("Disc", "Other"),
                             index = None,
                             placeholder = "Make selection...",
                             key = "q4_shape")

            with q4_col2:
                st.selectbox("Work shown",
                             ("fc","pc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q4_wrk")

            st.markdown("**Question 5**")
            q5_col1, q5_col2 = st.columns(2)

            with q5_col1:
                st.selectbox("Sorted?",
                             ("Yes","No"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q5a")
            with q5_col2:
                st.selectbox("Motivation",
                             ("fc","pc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q5b")

            st.markdown("**Question 6**")
            q6_col1, q6_col2, q6_col3 = st.columns(3)

            with q6_col1:
                st.selectbox("Soil texture class",
                             ("Sandy loam", "Other"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q6a")

            with q6_col2:
                st.selectbox("Texture",
                             ("Moderately coarse", "Other"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q6b")

            with q6_col3:
                st.selectbox("Common Name",
                             ("Loamy soils", "Other"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q6c")

            st.markdown("**Question 7**")
            q7_col1, q7_col2, q7_col3, q7_col4 = st.columns(4)

            with q7_col1:
                st.text_input("Penetration Resistance", key = "q7a")

            with q7_col2:
                st.selectbox("Units",
                             ("fc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q7a_unt")

            with q7_col3:
                st.selectbox("Site",
                             ("Site A", "Site B"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q7b")

            with q7_col4:
                st.selectbox("Motivation",
                             ("fc", "pc", "nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q7c")

            st.markdown("**Question 8**")
            q8_col1, q8_col2, q8_col3, q8_col4 = st.columns(4)

            with q8_col1:
                st.text_input("Plastic limit", key = "q8a")
                st.text_input("Plasticity index", key = "q8c")

            with q8_col2:
                st.selectbox("Units",
                             ("fc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q8a_unt")
                st.selectbox("Units",
                             ("fc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q8c_unt")

            with q8_col3:
                st.text_input("Liquid limit", key = "q8b")

            with q8_col4:
                st.selectbox("Units",
                             ("fc","nc"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q8b_unt")


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
            meta_info.add_text("q1", str(st.session_state["q1_grade"]))
            meta_info.add_text("q2", str(st.session_state["q2_grade"]))  
            meta_info.add_text("q3", str(st.session_state["q3_grade"]))  
            meta_info.add_text("q4", str(st.session_state["q4_grade"]))  
            meta_info.add_text("q5", str(st.session_state["q5_grade"]))  
            meta_info.add_text("q6", str(st.session_state["q6_grade"]))  
            meta_info.add_text("q7", str(st.session_state["q7_grade"]))  
            meta_info.add_text("q8", str(st.session_state["q8_grade"]))
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)

