import streamlit as st
import cv2 as cv
import pandas as pd
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import io
from io import BytesIO
from streamlit_image_zoom import image_zoom
import streamlit.components.v1 as components
import base64
from datetime import datetime
import textwrap
import yaml
from streamlit_gsheets import GSheetsConnection
from pathlib import Path
import gc

BASE_DIR = Path(__file__).resolve().parent.parent

# custom functions
# ------------------------------------------------------------
def submission_viewer(img_url, height=700, max_zoom_ratio=4.0, key="osd_viewer"):
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

def grade_submission():
    with open(BASE_DIR / "memo-practical-assignment-4.yaml", "r", encoding="utf-8") as file:
        memo = yaml.safe_load(file)

    q1 = {
        "q"        : ["a","b","c","d"],
        "dist_ans" : [memo["q1a"]["ans"],
                      memo["q1b"]["ans"],
                      memo["q1c"]["ans"],
                      memo["q1d"]["ans"]],
        "dist_fc"  : [memo["q1a"]["fc"],
                      memo["q1b"]["fc"],
                      memo["q1c"]["fc"],
                      memo["q1d"]["fc"]],
        "dist_pc"  : [memo["q1a"]["pc"],
                      memo["q1b"]["pc"],
                      memo["q1c"]["pc"],
                      memo["q1d"]["pc"]],
        "dist_sub" : [st.session_state["q1a_val"],
                      st.session_state["q1b_val"],
                      st.session_state["q1c_val"],
                      st.session_state["q1d_val"]],
        "dist_unt" : [st.session_state["q1a_unt"],
                      st.session_state["q1b_unt"],
                      st.session_state["q1c_unt"],
                      st.session_state["q1d_unt"]],
        "grade"    : [0.0,0.0,0.0,0.0]
    }

    q1 = pd.DataFrame(q1)
    try:
        q1["dist_sub"] = pd.to_numeric(q1["dist_sub"])
    except:
        st.error("Incorrect distance value format for question 1.")

    q1_dist_fc = q1["dist_sub"].between(q1["dist_ans"] - q1["dist_fc"],
                                        q1["dist_ans"] + q1["dist_fc"])
    q1_dist_pc = q1["dist_sub"].between(q1["dist_ans"] - q1["dist_pc"],
                                        q1["dist_ans"] + q1["dist_pc"])
    q1_dist_opt = [q1_dist_fc, q1_dist_pc]
    q1_dist_grd = [1.0, 0.5]
    q1["grade"] += np.select(q1_dist_opt, q1_dist_grd, default=0.0)
    q1["grade"] += (q1["dist_unt"] == "Full Credit").astype(float)

    st.session_state["q1a"] = q1.loc[q1["q"] == "a", "grade"].item()
    st.session_state["q1b"] = q1.loc[q1["q"] == "b", "grade"].item()
    st.session_state["q1c"] = q1.loc[q1["q"] == "c", "grade"].item()
    st.session_state["q1d"] = q1.loc[q1["q"] == "d", "grade"].item()
    st.session_state["q1_grade"] = q1["grade"].sum()

    cv.putText(warped_img, str(st.session_state["q1a"]),(2330,501),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q1b"]),(2330,633),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q1c"]),(2330,764),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q1d"]),(2330,908),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    q2 = {
        "q" : ["a","b"],
        "dist_ans" : [memo["q2a"]["ans"],
                      memo["q2b"]["ans"]],
        "dist_fc"  : [memo["q2a"]["fc"],
                      memo["q2b"]["fc"]],
        "dist_pc"  : [memo["q2a"]["pc"],
                      memo["q2b"]["pc"]],
        "dist_sub" : [st.session_state["q2a_val"],
                      st.session_state["q2b_val"]],
        "dist_unt" : [st.session_state["q2a_unt"],
                      st.session_state["q2b_unt"]],
        "dist_wrk" : [st.session_state["q2a_wrk"],
                      st.session_state["q2b_wrk"]],
        "grade"    : [0.0,0.0]
    }

    q2 = pd.DataFrame(q2)
    try:
        q2["dist_sub"] = pd.to_numeric(q2["dist_sub"])
    except:
        st.error("Incorrect distance value format for question 2.")

    q2_dist_fc = q2["dist_sub"].between(q2["dist_ans"] - q2["dist_fc"],
                                        q2["dist_ans"] + q2["dist_fc"])
    q2_dist_pc = q2["dist_sub"].between(q2["dist_ans"] - q2["dist_pc"],
                                        q2["dist_ans"] + q2["dist_pc"])
    q2_dist_opt = [q2_dist_fc, q2_dist_pc]
    q2_dist_grd = [2.0,1.0]
    q2["grade"] += np.select(q2_dist_opt, q2_dist_grd, default = 0.0)

    q2["grade"] += (q2["dist_unt"] == "Full Credit").astype(float)

    q2_wrk_fc = q2["dist_wrk"] == "Full Credit"
    q2_wrk_pc = q2["dist_wrk"] == "Partial Credit"
    q2_wrk_nc = q2["dist_wrk"] == "No Credit"
    q2_wrk_opt = [q2_wrk_fc, q2_wrk_pc, q2_wrk_nc]
    q2_wrk_grd = [1.0, 0.5, 0.0]
    q2["grade"] += np.select(q2_wrk_opt, q2_wrk_grd, default = 0.0)

    st.session_state["q2a"] = q2.loc[q2["q"] == "a", "grade"].item()
    st.session_state["q2b"] = q2.loc[q2["q"] == "b", "grade"].item()
    st.session_state["q2_grade"] = q2["grade"].sum()

    cv.putText(warped_img, str(st.session_state["q2a"]),(2330,1245),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q2b"]),(2330,1382),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["final_grade"] = st.session_state["q1_grade"] + st.session_state["q2_grade"]

    st.session_state["final_grade_prcnt"] = (st.session_state["final_grade"] / 16) * 100 

    conn = st.connection("gsheets", type=GSheetsConnection)
    gc = conn.read(ttl=0)
    column_name = "Practical assignment 4 [Total Pts: 16 Percentage] |2934610"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade_prcnt"]
    conn.update(data=gc)
    
    cv.putText(warped_img, str(st.session_state["final_grade"]),(855,455),cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["student"]),(301,244),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
        
    st.session_state["graded_submission"] = warped_img

def next_submission():
    st.session_state["script_index"] += 1
    st.session_state["q1a_val"] = ""
    st.session_state["q1b_val"] = ""
    st.session_state["q1c_val"] = ""
    st.session_state["q1d_val"] = ""
    st.session_state["q1a_unt"] = None
    st.session_state["q1b_unt"] = None
    st.session_state["q1c_unt"] = None
    st.session_state["q1d_unt"] = None
    st.session_state["q2a_val"] = ""
    st.session_state["q2b_val"] = ""
    st.session_state["q2a_unt"] = None
    st.session_state["q2b_unt"] = None
    st.session_state["q2a_wrk"] = None
    st.session_state["q2b_wrk"] = None
    del st.session_state["graded_submission"]
    
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
    st.image(BASE_DIR / "NAS_Faculty Logo.jpg")

with title_col2:
    st.title("GGY 168 — Introduction to Physical Geography")
    st.header("Practical Assignment 4 — Distance")

with st.expander("Instructions", expanded = False):
    st.markdown(textwrap.dedent("""
    1. Enter your name in the provided field.
    2. Load the student submission. It is now possible to load multiple submissions at the same time, which should speed up grading.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. For question 2 in the "Work" column, assign values based on the following:
        - "Full Credit": Three or more of the line intersection marks occur within the red circles.
        - "Partial Credit": Line intersection marks are present, but fewer than three fall into the red circles.
        - "No Credit": No line intersection marks are present.
    8. When you are done, press the grade button.
    9. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
    10. If you uploaded multiple submissions, press the next button.
    """))

if "script_index" not in st.session_state:
    st.session_state["script_index"] = 0

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# load class list and submission
with st.sidebar:
    grader = st.text_input("Name of grader", key="graderName")
    pin = st.text_input("Enter PIN number",
                        type = "password",
                        key = "user_pin_pa4")
    uploaded_files = st.file_uploader("Select the student submission",
                                      type = ["png"],
                                      accept_multiple_files = True,
                                      key = str(st.session_state["uploader_key"]))
    st.button("Clear", on_click = clear_files)

valid_pin_pa4 = st.secrets.get("secret_pin_pa4")
    
if uploaded_files and grader.strip() and st.session_state["user_pin_pa4"].strip() == valid_pin_pa4:
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

        ac = pd.read_csv(BASE_DIR / "aruco-practical-assignment-4.csv")

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
        del cv_img
        gc.collect()
        
        # load intersections files
        shift = 8
        factor = 1 << shift
        bubble_radius = int(round(24 * factor))
        ov = pd.read_csv(BASE_DIR / "oak_to_val.csv")
        iu = pd.read_csv(BASE_DIR / "iro_to_upt.csv")

        for i in range(len(ov)):
            rawx = ov.iloc[i]["cvx"]
            rawy = ov.iloc[i]["cvy"]
            ovx = int(round(rawx * factor))
            ovy = int(round(rawy * factor))
            cv.circle(warped_img, (ovx, ovy), bubble_radius, (0,0,255), 2, shift = shift)

        for i in range(len(iu)):
            rawx = iu.iloc[i]["cvx"]
            rawy = iu.iloc[i]["cvy"]
            iux = int(round(rawx * factor))
            iuy = int(round(rawy * factor))
            cv.circle(warped_img, (iux, iuy), bubble_radius, (0,0,255), 2, shift = shift)

        _, disp_img = cv.imencode(".jpg",warped_img, [int(cv.IMWRITE_JPEG_QUALITY), 80])
        b64_str = base64.b64encode(disp_img).decode("utf-8")
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

        with st.expander("Question 1", expanded = False):
            q1_col1, q1_col2 = st.columns(2)

            with q1_col1:
                st.markdown("**Distance**")
                st.text_input("Question 1(a)", key = "q1a_val")
                st.text_input("Question 1(b)", key = "q1b_val")
                st.text_input("Question 1(c)", key = "q1c_val")
                st.text_input("Question 1(d)", key = "q1d_val")

            with q1_col2:
                st.markdown("**Units**")
                st.selectbox("Question 1(a)",
                             ("Full Credit","No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q1a_unt")
                st.selectbox("Question 1(b)",
                             ("Full Credit","No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q1b_unt")
                st.selectbox("Question 1(c)",
                             ("Full Credit","No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q1c_unt")
                st.selectbox("Question 1(d)",
                             ("Full Credit","No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q1d_unt")

        with st.expander("Question 2", expanded = False):
            q2_col1, q2_col2, q2_col3 = st.columns(3)

            with q2_col1:
                st.markdown("**Distance**")
                st.text_input("Oakhaven to Vale", key = "q2a_val")
                st.text_input("Ironside to Upton", key = "q2b_val")

            with q2_col2:
                st.markdown("**Units**")
                st.selectbox("Oakhaven to Valen",
                             ("Full Credit", "No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q2a_unt")
                st.selectbox("Ironside to Upton",
                             ("Full Credit", "No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q2b_unt")

            with q2_col3:
                st.markdown("**Work**")
                st.selectbox("Oakhaven to Valen",
                             ("Full Credit", "Partial Credit", "No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q2a_wrk")
                st.selectbox("Ironside to Upton",
                             ("Full Credit", "Partial Credit", "No Credit"),
                             index = None,
                             placeholder = "Make a selection...",
                             key = "q2b_wrk")

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
            meta_info.add_text("q1", str(st.session_state["q1_grade"]))
            meta_info.add_text("q2", str(st.session_state["q2_grade"]))
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
            
