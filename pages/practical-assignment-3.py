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

def safe_float(val):
    try:
        val_str = str(val).strip()
        return float(val_str) if val_str else None
    except:
        return None
    
def grade_submission():
    q1_memo = pd.read_csv(BASE_DIR / "practical-assignment-3-question-1-memo.csv")
    
    q1_ans = {
        "q" : ["a","b","c"],
        "tfb_val" : [safe_float(st.session_state["q1a_tfb_val"]),
                     safe_float(st.session_state["q1b_tfb_val"]),
                     safe_float(st.session_state["q1c_tfb_val"])],
        "tfb_unt" : [st.session_state["q1a_tfb_unt"],
                     st.session_state["q1b_tfb_unt"],
                     st.session_state["q1c_tfb_unt"]],
        "tbb_val" : [safe_float(st.session_state["q1a_tbb_val"]),
                     safe_float(st.session_state["q1b_tbb_val"]),
                     safe_float(st.session_state["q1c_tbb_val"])],
        "tbb_unt" : [st.session_state["q1a_tbb_unt"],
                     st.session_state["q1b_tbb_unt"],
                     st.session_state["q1c_tbb_unt"]],
        "grade" : [0.0,0.0,0.0]
    }

    q1_ans = pd.DataFrame(q1_ans)
    q1 = pd.merge(q1_memo, q1_ans, on = "q", how = "inner")

    tfb_fc = q1["tfb_val"].between(q1["tfb"] - q1["fc"], q1["tfb"] + q1["fc"])
    tfb_pc = q1["tfb_val"].between(q1["tfb"] - q1["pc"], q1["tfb"] + q1["pc"])
    tfb_opt = [tfb_fc, tfb_pc]
    tfb_grd = [0.5, 0.25]
    q1["grade"] += np.select(tfb_opt, tfb_grd, default = 0.0)

    tbb_fc = q1["tbb_val"].between(q1["tbb"] - q1["fc"], q1["tbb"] + q1["fc"])
    tbb_pc = q1["tbb_val"].between(q1["tbb"] - q1["pc"], q1["tbb"] + q1["pc"])
    tbb_opt = [tbb_fc, tbb_pc]
    tbb_grd = [0.5, 0.25]
    q1["grade"] += np.select(tbb_opt, tbb_grd, default = 0.0)

    q1["grade"] += (q1["tfb_unt"] == "Full Credit").astype(float) / 2.0
    q1["grade"] += (q1["tbb_unt"] == "Full Credit").astype(float) / 2.0

    st.session_state["q1a"] = q1.loc[q1["q"] == "a", "grade"].item()
    st.session_state["q1b"] = q1.loc[q1["q"] == "b", "grade"].item()
    st.session_state["q1c"] = q1.loc[q1["q"] == "c", "grade"].item()
    st.session_state["q1_total"] = q1["grade"].sum()

    cv.putText(warped_img, str(st.session_state["q1a"]),(2361,1554),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q1b"]),(2361,1629),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q1c"]),(2361,1704),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    # ============================================================

    q2_memo = pd.read_csv(BASE_DIR / "practical-assignment-3-question-2-memo.csv")
    q2_ans = {
        "q" : ["a","b","c"],
        "sub_ans" : [safe_float(st.session_state["q2a_val"]),
                     safe_float(st.session_state["q2b_val"]),
                     safe_float(st.session_state["q2c_val"])],
        "sub_unt" : [st.session_state["q2a_unt"],
                     st.session_state["q2b_unt"],
                     st.session_state["q2c_unt"]],
        "grade" : [0.0,0.0,0.0]
    }

    q2_ans = pd.DataFrame(q2_ans)
    q2 = pd.merge(q2_memo, q2_ans, on = "q", how = "inner")

    q2_ans_fc = q2["sub_ans"].between(q2["ans"] - q2["fc"], q2["ans"] + q2["fc"])
    q2_ans_pc = q2["sub_ans"].between(q2["ans"] - q2["pc"], q2["ans"] + q2["pc"])
    q2_ans_opt = [q2_ans_fc, q2_ans_pc]
    q2_ans_grd = [1.0, 0.5]
    q2["grade"] += np.select(q2_ans_opt, q2_ans_grd, default = 0.0)

    q2["grade"] += (q2["sub_unt"] == "Full Credit").astype(float)

    st.session_state["q2a"] = q2.loc[q2["q"] == "a", "grade"].item()
    st.session_state["q2b"] = q2.loc[q2["q"] == "b", "grade"].item()
    st.session_state["q2c"] = q2.loc[q2["q"] == "c", "grade"].item()
    st.session_state["q2_total"] = q2["grade"].sum()

    cv.putText(warped_img, str(st.session_state["q2a"]),(2361,2023),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q2b"]),(2361,2104),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q2c"]),(2361,2185),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    # ============================================================

    q3_memo = pd.read_csv(BASE_DIR / "practical-assignment-3-question-3-memo.csv")
    q3_ans = {
        "q" : ["a","b","c"],
        "tfb_val" : [safe_float(st.session_state["q3a_tfb_val"]),
                     safe_float(st.session_state["q3b_tfb_val"]),
                     safe_float(st.session_state["q3c_tfb_val"])],
        "tfb_unt" : [st.session_state["q3a_tfb_unt"],
                     st.session_state["q3b_tfb_unt"],
                     st.session_state["q3c_tfb_unt"]],
        "tbb_val" : [safe_float(st.session_state["q3a_tbb_val"]),
                     safe_float(st.session_state["q3b_tbb_val"]),
                     safe_float(st.session_state["q3c_tbb_val"])],
        "tbb_unt" : [st.session_state["q3a_tbb_unt"],
                     st.session_state["q3b_tbb_unt"],
                     st.session_state["q3c_tbb_unt"]],
        "grade" : [0.0,0.0,0.0]
    }

    q3_ans = pd.DataFrame(q3_ans)
    q3 = pd.merge(q3_memo, q3_ans, on = "q", how = "inner")

    tfb_fc = q3["tfb_val"].between(q3["tfb"] - q3["fc"], q3["tfb"] + q3["fc"])
    tfb_pc = q3["tfb_val"].between(q3["tfb"] - q3["pc"], q3["tfb"] + q3["pc"])
    tfb_opt = [tfb_fc, tfb_pc]
    tfb_grd = [0.5, 0.25]
    q3["grade"] += np.select(tfb_opt, tfb_grd, default = 0.0)

    tbb_fc = q3["tbb_val"].between(q3["tbb"] - q3["fc"], q3["tbb"] + q3["fc"])
    tbb_pc = q3["tbb_val"].between(q3["tbb"] - q3["pc"], q3["tbb"] + q3["pc"])
    tbb_opt = [tbb_fc, tbb_pc]
    tbb_grd = [0.5, 0.25]
    q3["grade"] += np.select(tbb_opt, tbb_grd, default = 0.0)

    q3["grade"] += (q3["tfb_unt"] == "Full Credit").astype(float) / 2.0
    q3["grade"] += (q3["tbb_unt"] == "Full Credit").astype(float) / 2.0

    st.session_state["q3a"] = q3.loc[q3["q"] == "a", "grade"].item()
    st.session_state["q3b"] = q3.loc[q3["q"] == "b", "grade"].item()
    st.session_state["q3c"] = q3.loc[q3["q"] == "c", "grade"].item()
    st.session_state["q3_total"] = q3["grade"].sum()

    cv.putText(warped_img, str(st.session_state["q3a"]),(2361,2492),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q3b"]),(2361,2573),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q3c"]),(2361,2654),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    # ============================================================

    q4_memo = pd.read_csv(BASE_DIR / "practical-assignment-3-question-4-memo.csv")
    q4_ans = {
        "q" : ["a","b","c"],
        "mfb_val" : [safe_float(st.session_state["q4a_mfb_val"]),
                     safe_float(st.session_state["q4b_mfb_val"]),
                     safe_float(st.session_state["q4c_mfb_val"])],
        "mfb_unt" : [st.session_state["q4a_mfb_unt"],
                     st.session_state["q4b_mfb_unt"],
                     st.session_state["q4c_mfb_unt"]],
        "mbb_val" : [safe_float(st.session_state["q4a_mbb_val"]),
                     safe_float(st.session_state["q4b_mbb_val"]),
                     safe_float(st.session_state["q4c_mbb_val"])],
        "mbb_unt" : [st.session_state["q4a_mbb_unt"],
                     st.session_state["q4b_mbb_unt"],
                     st.session_state["q4c_mbb_unt"]],
        "grade" : [0.0,0.0,0.0]
    }

    q4_ans = pd.DataFrame(q4_ans)
    q4 = pd.merge(q4_memo, q4_ans, on = "q", how = "inner")

    mfb_fc = q4["mfb_val"].between(q4["mfb"] - q4["fc"], q4["mfb"] + q4["fc"])
    mfb_pc = q4["mfb_val"].between(q4["mfb"] - q4["pc"], q4["mfb"] + q4["pc"])
    mfb_opt = [mfb_fc, mfb_pc]
    mfb_grd = [0.5, 0.25]
    q4["grade"] += np.select(mfb_opt, mfb_grd, default = 0.0)

    mbb_fc = q4["mbb_val"].between(q4["mbb"] - q4["fc"], q4["mbb"] + q4["fc"])
    mbb_pc = q4["mbb_val"].between(q4["mbb"] - q4["pc"], q4["mbb"] + q4["pc"])
    mbb_opt = [mbb_fc, mbb_pc]
    mbb_grd = [0.5, 0.25]
    q4["grade"] += np.select(mbb_opt, mbb_grd, default = 0.0)

    q4["grade"] += (q4["mfb_unt"] == "Full Credit").astype(float) / 2.0
    q4["grade"] += (q4["mbb_unt"] == "Full Credit").astype(float) / 2.0

    st.session_state["q4a"] = q4.loc[q4["q"] == "a", "grade"].item()
    st.session_state["q4b"] = q4.loc[q4["q"] == "b", "grade"].item()
    st.session_state["q4c"] = q4.loc[q4["q"] == "c", "grade"].item()
    st.session_state["q4_total"] = q4["grade"].sum()

    st.session_state["final_grade_prcnt"] = (st.session_state["q4_total"] / 24) * 100

    conn = st.connection("gsheets", type=GSheetsConnection)
    gc = conn.read(ttl=0)
    column_name = "Practical assignment 3 [Total Pts: 24 Percentage] |2934609"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade_prcnt"]
    conn.update(data=gc)

    cv.putText(warped_img, str(st.session_state["q4a"]),(2361,2967),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q4b"]),(2361,3047),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["q4c"]),(2361,3123),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["final_grade"] = st.session_state["q1_total"] + st.session_state["q2_total"] + st.session_state["q3_total"] + st.session_state["q4_total"]

    cv.putText(warped_img, str(st.session_state["final_grade"]),(852,455),cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(warped_img, str(st.session_state["student"]),(301,244),cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = warped_img

def dms_to_dd():
    raw = st.session_state["conv_dms"].strip()
    parts = raw.split("/")
    nums = [float(p) for p in parts]
    if len(nums) != 3:
        st.error("Incorrect DMS entry. Entry must be dd/mm/ss (if there are no seconds, just enter 00).")
    else:
        try:
            deg, minutes, sec = [float(p) for p in parts]
            dd = round(deg + (minutes / 60.0) + (sec / 3600.0), 4)
            st.session_state["conv_ans"] = f"{dd}"
        except:
            st.error("Incorrect data entered.")

def next_submission():
    st.session_state["script_index"] += 1
    st.session_state["q1a_tfb_val"] = ""
    st.session_state["q1b_tfb_val"] = ""
    st.session_state["q1c_tfb_val"] = ""
    st.session_state["q1a_tfb_unt"] = None
    st.session_state["q1b_tfb_unt"] = None
    st.session_state["q1c_tfb_unt"] = None
    st.session_state["q1a_tbb_val"] = ""
    st.session_state["q1b_tbb_val"] = ""
    st.session_state["q1c_tbb_val"] = ""
    st.session_state["q1a_tbb_unt"] = None
    st.session_state["q1b_tbb_unt"] = None
    st.session_state["q1c_tbb_unt"] = None
    st.session_state["q2a_val"] = ""
    st.session_state["q2b_val"] = ""
    st.session_state["q2c_val"] = ""
    st.session_state["q2a_unt"] = None
    st.session_state["q2b_unt"] = None
    st.session_state["q2c_unt"] = None
    st.session_state["q3a_tfb_val"] = ""
    st.session_state["q3b_tfb_val"] = ""
    st.session_state["q3c_tfb_val"] = ""
    st.session_state["q3a_tfb_unt"] = None
    st.session_state["q3b_tfb_unt"] = None
    st.session_state["q3c_tfb_unt"] = None
    st.session_state["q3a_tbb_val"] = ""
    st.session_state["q3b_tbb_val"] = ""
    st.session_state["q3c_tbb_val"] = ""
    st.session_state["q3a_tbb_unt"] = None
    st.session_state["q3b_tbb_unt"] = None
    st.session_state["q3c_tbb_unt"] = None
    st.session_state["q4a_mfb_val"] = ""
    st.session_state["q4b_mfb_val"] = ""
    st.session_state["q4c_mfb_val"] = ""
    st.session_state["q4a_mfb_unt"] = None
    st.session_state["q4b_mfb_unt"] = None
    st.session_state["q4c_mfb_unt"] = None
    st.session_state["q4a_mbb_val"] = ""
    st.session_state["q4b_mbb_val"] = ""
    st.session_state["q4c_mbb_val"] = ""
    st.session_state["q4a_mbb_unt"] = None
    st.session_state["q4b_mbb_unt"] = None
    st.session_state["q4c_mbb_unt"] = None
    st.session_state["conv_dms"] = ""
    st.session_state["conv_ans"] = ""

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
    st.header("Practical Assignment 3 — Direction")


with st.expander("Instructions", expanded = False):
    st.markdown(textwrap.dedent("""
    1. Enter your name in the provided field.
    2. Load the student submission. It is now possible to load multiple submissions at the same time which should make the grading faster.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. The following symbols are used:
       - $T_{fb}$ for True forward bearing.
       - $T_{bb}$ for True backward bearing.
       - $M_{fb}$ for Magnetic forward bearing.
       - $M_{bb}$ for Magnetic backward bearing.
    7. If the bearing is provided in degrees, minutes, and seconds (DMS) use the calculator at the bottom of the page to convert the answer to decimal degrees. Copy this answer to the appropriate field. To use the calculator, a complete DMS record must be entered deg/min/sec (note the forward slashes separating the values).
    8. When you are done, press the grade button.
    9. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
    10. If you uploaded multiplee submissions, press the next buttun.
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
                        key = "user_pin_pa3")
    uploaded_files = st.file_uploader("Select the student submission",
                                      type = ["png"],
                                      accept_multiple_files = True,
                                      key = str(st.session_state["uploader_key"]))
    st.button("Clear", on_click = clear_files)

valid_pin_pa3 = st.secrets.get("secret_pin_pa3")
    
if uploaded_files and grader.strip() and st.session_state["user_pin_pa3"].strip() == valid_pin_pa3:
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
        topleft_x = int(np.mean(aruco_0_corners_rshp[:,0]))
        topleft_y = int(np.mean(aruco_0_corners_rshp[:,1]))

        aruco_1_index = ids.index(1)
        aruco_1_corners = corners[aruco_1_index]
        aruco_1_corners_rshp = aruco_1_corners.reshape((4,2))
        topright_x = int(np.mean(aruco_1_corners_rshp[:,0]))
        topright_y = int(np.mean(aruco_1_corners_rshp[:,1]))

        aruco_2_index = ids.index(2)
        aruco_2_corners = corners[aruco_2_index]
        aruco_2_corners_rshp = aruco_2_corners.reshape((4,2))
        bottomleft_x = int(np.mean(aruco_2_corners_rshp[:,0]))
        bottomleft_y = int(np.mean(aruco_2_corners_rshp[:,1]))

        aruco_3_index = ids.index(3)
        aruco_3_corners = corners[aruco_3_index]
        aruco_3_corners_rshp = aruco_3_corners.reshape((4,2))
        bottomright_x = int(np.mean(aruco_3_corners_rshp[:,0]))
        bottomright_y = int(np.mean(aruco_3_corners_rshp[:,1]))

        # Prepare the image for warping
        current_coords = np.float32([[topleft_x, topleft_y],
                                     [topright_x, topright_y],
                                     [bottomright_x, bottomright_y],
                                     [bottomleft_x, bottomleft_y]])

        ac = pd.read_csv(BASE_DIR / "aruco-practical-assignment-3.csv")
                
        target_coords = np.float32([[ac.iloc[0,3], ac.iloc[0,4]],
                                    [ac.iloc[1,3], ac.iloc[1,4]],
                                    [ac.iloc[3,3], ac.iloc[3,4]],
                                    [ac.iloc[2,3], ac.iloc[2,4]]])
        
        transformation_matrix = cv.getPerspectiveTransform(current_coords,
                                                           target_coords)

        # transform the image
        warped_img = cv.warpPerspective(cv_img,
                                        transformation_matrix,
                                        (2480,3508),
                                        borderMode=cv.BORDER_CONSTANT,
                                        borderValue=(255, 255, 255))
        del cv_img
        gc.collect()

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
            q1_col1, q1_col2, q1_col3, q1_col4 = st.columns(4)

            with q1_col1:
                st.markdown("$T_{fb}$")
                st.markdown("*Degrees*")
                st.text_input("A to B", key="q1a_tfb_val")
                st.text_input("C to D", key="q1b_tfb_val")
                st.text_input("E to F", key="q1c_tfb_val")

            with q1_col2:
                st.markdown("$T_{fb}$")
                st.markdown("*Units*")
                st.selectbox("A to B", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1a_tfb_unt")
                st.selectbox("C to D", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1b_tfb_unt")
                st.selectbox("E to F", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1c_tfb_unt")

            with q1_col3:                       
                st.markdown("$T_{bb}$")
                st.markdown("*Degrees*")
                st.text_input("A to B", key="q1a_tbb_val")
                st.text_input("C to D", key="q1b_tbb_val")
                st.text_input("E to F", key="q1c_tbb_val")
                                                    
            with q1_col4:                       
                st.markdown("$T_{bb}$")
                st.markdown("*Units*")
                st.selectbox("A to B", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1a_tbb_unt")
                st.selectbox("C to D", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1b_tbb_unt")
                st.selectbox("E to F", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q1c_tbb_unt")

        with st.expander("Question 2", expanded = False):
            q2_col1, q2_col2 = st.columns(2)

            with q2_col1:
                st.markdown("Declination")
                st.text_input("Question 2a)", key = "q2a_val")
                st.text_input("Question 2b)", key = "q2b_val")
                st.text_input("Question 2c)", key = "q2c_val")

            with q2_col2:
                st.markdown("Units")
                st.selectbox("Question 2a)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection...", key = "q2a_unt")
                st.selectbox("Question 2b)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection...", key = "q2b_unt")
                st.selectbox("Question 2c)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection...", key = "q2c_unt")

        with st.expander("Question 3", expanded = False):
            q3_col1, q3_col2, q3_col3, q3_col4 = st.columns(4)

            with q3_col1:
                st.markdown("$T_{fb}$")
                st.markdown("*Degrees*")
                st.text_input("Question 3a)", key="q3a_tfb_val")
                st.text_input("Question 3b)", key="q3b_tfb_val")
                st.text_input("Question 3c)", key="q3c_tfb_val")

            with q3_col2:
                st.markdown("$T_{fb}$")
                st.markdown("*Units*")
                st.selectbox("Question 3a)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3a_tfb_unt")
                st.selectbox("Question 3b)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3b_tfb_unt")
                st.selectbox("Question 3c)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3c_tfb_unt")

            with q3_col3:                       
                st.markdown("$T_{bb}$")
                st.markdown("*Degrees*")
                st.text_input("Question 3a)", key="q3a_tbb_val")
                st.text_input("Question 3b)", key="q3b_tbb_val")
                st.text_input("Question 3c)", key="q3c_tbb_val")
                                                    
            with q3_col4:                       
                st.markdown("$T_{bb}$")
                st.markdown("*Units*")
                st.selectbox("Question 3a)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3a_tbb_unt")
                st.selectbox("Question 3b)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3b_tbb_unt")
                st.selectbox("Question 3c)", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q3c_tbb_unt")

        with st.expander("Question 4", expanded = False):
            q4_col1, q4_col2, q4_col3, q4_col4 = st.columns(4)

            with q4_col1:
                st.markdown("$M_{fb}$")
                st.markdown("*Degrees*")
                st.text_input("B to A", key="q4a_mfb_val")
                st.text_input("D to C", key="q4b_mfb_val")
                st.text_input("F to E", key="q4c_mfb_val")

            with q4_col2:
                st.markdown("$M_{fb}$")
                st.markdown("*Units*")
                st.selectbox("B to A", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4a_mfb_unt")
                st.selectbox("D to C", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4b_mfb_unt")
                st.selectbox("F to E", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4c_mfb_unt")

            with q4_col3:                       
                st.markdown("$M_{bb}$")
                st.markdown("*Degrees*")
                st.text_input("B to A", key="q4a_mbb_val")
                st.text_input("D to C", key="q4b_mbb_val")
                st.text_input("F to E", key="q4c_mbb_val")
                                                    
            with q4_col4:                       
                st.markdown("$M_{bb}$")
                st.markdown("*Units*")
                st.selectbox("B to A", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4a_mbb_unt")
                st.selectbox("D to C", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4b_mbb_unt")
                st.selectbox("F to E", ("Full Credit", "Other"), index = None, placeholder = "Make a selection..", key="q4c_mbb_unt")

        with st.expander("DMS to DD Converter", expanded = False):
            conv_col1, conv_col2, conv_col3 = st.columns([2,1,2], vertical_alignment="bottom")

            with conv_col1:
                st.text_input("(deg/min/sec)", key="conv_dms")

            with conv_col2:
                st.button("Convert", on_click=dms_to_dd)
                
            with conv_col3:
                st.text_input("Decimal Degrees", key="conv_ans")

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
            meta_info.add_text("q3", str(st.session_state["q3_total"]))
            meta_info.add_text("q4", str(st.session_state["q4_total"]))
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
            
