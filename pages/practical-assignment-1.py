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

# ------------------------------------------------------------
def grade_submission():
    q1 = {
        "q"            : ["a","b","c","d"],
        "mem_lat"      : [42.5725, 51.2419, 72.2795, 15.1430],
        "fc_lat_U"     : [42.5727, 51.2421, 72.2797, 15.1432],
        "fc_lat_L"     : [42.5723, 51.2417, 72.2793, 15.1428],
        "pc_lat_U"     : [42.5729, 51.2423, 72.2799, 15.1434],
        "pc_lat_L"     : [42.5721, 51.2415, 72.2791, 15.1426],
        "sub_lat"      : [float(st.session_state["one_a_lat"]),
                          float(st.session_state["one_b_lat"]),
                          float(st.session_state["one_c_lat"]),
                          float(st.session_state["one_d_lat"])],
        "mem_lon"      : [47.2889, 40.5508, 115.3131, 112.3586],
        "fc_lon_U"     : [47.2891, 40.551, 115.3133, 112.3588],
        "fc_lon_L"     : [47.2887, 40.5506, 115.3129, 112.3584],
        "pc_lon_U"     : [47.2893, 40.5512, 115.3135, 112.359],
        "pc_lon_L"     : [47.2885, 40.5504, 115.3127, 112.3582],
        "sub_lon"      : [float(st.session_state["one_a_lon"]),
                          float(st.session_state["one_b_lon"]),
                          float(st.session_state["one_c_lon"]),
                          float(st.session_state["one_d_lon"])],
        "mem_lat_card" : ["S", "S", "N", "N"],
        "sub_lat_card" : [st.session_state["one_a_lat_dir"],
                          st.session_state["one_b_lat_dir"],
                          st.session_state["one_c_lat_dir"],
                          st.session_state["one_d_lat_dir"]],
        "mem_lon_card" : ["E", "W", "E", "W"],
        "sub_lon_card" : [st.session_state["one_a_lon_dir"],
                          st.session_state["one_b_lon_dir"],
                          st.session_state["one_c_lon_dir"],
                          st.session_state["one_d_lon_dir"]],
        "grade"        : [0.0, 0.0, 0.0, 0.0]
    }

    q1 = pd.DataFrame(q1)
    
    # latitude
    lat_fc = q1["sub_lat"].between(q1["fc_lat_L"], q1["fc_lat_U"])
    lat_pc = q1["sub_lat"].between(q1["pc_lat_L"], q1["pc_lat_U"])

    lat_opt = [lat_fc, lat_pc]
    lat_grd = [1.0, 0.5]
    q1["grade"] += np.select(lat_opt, lat_grd, default = 0.0)

    # longitude
    lon_fc = q1["sub_lon"].between(q1["fc_lon_L"], q1["fc_lon_U"])
    lon_pc = q1["sub_lon"].between(q1["pc_lon_L"], q1["pc_lon_U"])
    lon_opt = [lon_fc, lon_pc]
    lon_grd = [1.0, 0.5]
    q1["grade"] += np.select(lon_opt, lon_grd, default = 0.0)

    # cardinal direction
    lat_card_fc = q1["sub_lat_card"] == q1["mem_lat_card"]
    lat_card_nc = q1["sub_lat_card"] != q1["mem_lat_card"]
    lat_card_opt = [lat_card_fc, lat_card_nc]
    lat_card_grd = [1.0, 0.0]
    q1["grade"] += np.select(lat_card_opt, lat_card_grd, default = 0.0)

    # cardinal direction
    lon_card_fc = q1["sub_lon_card"] == q1["mem_lon_card"]
    lon_card_nc = q1["sub_lon_card"] != q1["mem_lon_card"]
    lon_card_opt = [lon_card_fc, lon_card_nc]
    lon_card_grd = [1.0, 0.0]
    q1["grade"] += np.select(lon_card_opt, lon_card_grd, default = 0.0)

    q2 = {
        "q" : ["a", "b", "c", "d"],
        "mem_lat_deg" : [5, 74, 42, 49],
        "mem_lat_min" : [1, 1, 42, 34],
        "mem_lat_sec" : [18, 46, 34, 43],
        "fc_lat_U"    : [19, 47, 35, 44],
        "fc_lat_L"    : [17, 45, 33, 42],
        "pc_lat_U"    : [20, 48, 36, 45],
        "pc_lat_L"    : [16, 44, 32, 41],
        "mem_lat_card": ["S", "S", "N", "N"],
        "mem_lon_deg" : [137, 121, 106, 96],
        "mem_lon_min" : [24, 38, 37, 10],
        "mem_lon_sec" : [49, 2, 12, 9],
        "fc_lon_U"    : [50, 3, 13, 10],
        "fc_lon_L"    : [48, 1, 11, 8],
        "pc_lon_U"    : [51, 4, 14, 11],
        "pc_lon_L"    : [47, 0, 10, 7],
        "mem_lon_card": ["E", "W", "E", "W"],
        "sub_lat"     : [st.session_state["two_a_lat"],
                         st.session_state["two_b_lat"],
                         st.session_state["two_c_lat"],
                         st.session_state["two_d_lat"]],
        "sub_lat_card": [st.session_state["two_a_lat_dir"],
                         st.session_state["two_b_lat_dir"],
                         st.session_state["two_c_lat_dir"],
                         st.session_state["two_d_lat_dir"]],
        "sub_lon"     : [st.session_state["two_a_lon"],
                         st.session_state["two_b_lon"],
                         st.session_state["two_c_lon"],
                         st.session_state["two_d_lon"]],
        "sub_lon_card": [st.session_state["two_a_lon_dir"],
                         st.session_state["two_b_lon_dir"],
                         st.session_state["two_c_lon_dir"],
                         st.session_state["two_d_lon_dir"]],
        "grade"       : [0.0, 0.0, 0.0, 0.0]
    }

    q2 = pd.DataFrame(q2)

    q2[["lat_deg", "lat_min", "lat_sec"]] = q2["sub_lat"].str.split("/", expand = True)
    q2[["lon_deg", "lon_min", "lon_sec"]] = q2["sub_lon"].str.split("/", expand = True)

    q2["lat_deg"] = pd.to_numeric(q2["lat_deg"])
    q2["lat_min"] = pd.to_numeric(q2["lat_min"])
    q2["lat_sec"] = pd.to_numeric(q2["lat_sec"])

    q2["lon_deg"] = pd.to_numeric(q2["lon_deg"])
    q2["lon_min"] = pd.to_numeric(q2["lon_min"])
    q2["lon_sec"] = pd.to_numeric(q2["lon_sec"])

    lat_deg_mod = (q2["lat_deg"] == q2["mem_lat_deg"]).astype(float)
    lat_min_mod = (q2["lat_min"] == q2["mem_lat_min"]).astype(float)
    lat_card = (q2["sub_lat_card"] == q2["mem_lat_card"]).astype(float)
    
    lon_deg_mod = (q2["lon_deg"] == q2["mem_lon_deg"]).astype(float)
    lon_min_mod = (q2["lon_min"] == q2["mem_lon_min"]).astype(float)
    lon_card = (q2["sub_lon_card"] == q2["mem_lon_card"]).astype(float)
    
    lat_sec_fc = q2["lat_sec"].between(q2["fc_lat_L"], q2["fc_lat_U"])
    lat_sec_pc = q2["lat_sec"].between(q2["pc_lat_L"], q2["pc_lat_U"])
    lon_sec_fc = q2["lon_sec"].between(q2["fc_lon_L"], q2["fc_lon_U"])
    lon_sec_pc = q2["lon_sec"].between(q2["pc_lon_L"], q2["pc_lon_U"])

    lat_sec_opt = [lat_sec_fc, lat_sec_pc]
    lon_sec_opt = [lon_sec_fc, lon_sec_pc]

    lat_sec_grd = [1.0, 0.5]
    lon_sec_grd = [1.0, 0.5]

    q2["grade"] += np.select(lat_sec_opt, lat_sec_grd, default = 0.0) * lat_deg_mod * lat_min_mod
    q2["grade"] += np.select(lon_sec_opt, lon_sec_grd, default = 0.0) * lon_deg_mod * lon_min_mod
    q2["grade"] += lat_card
    q2["grade"] += lon_card
    

    # assignment total
    total = float(q1["grade"].sum() + q2["grade"].sum())
    st.session_state["q1"] = str(float(q1["grade"].sum()))
    st.session_state["q2"] = str(float(q2["grade"].sum()))
    st.session_state["final"] = str(total)
    st.session_state["final_grade_prcnt"] = (total / 32) * 100

    conn = st.connection("gsheets", type=GSheetsConnection)
    gc = conn.read(ttl=0)
    column_name = "Practical assignment 1 [Total Pts: 32 Percentage] |2934606"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade_prcnt"]
    conn.update(data=gc)
    
    # add text to image
    cv.putText(warped_img, str(total), (824,446), cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(warped_img, st.session_state["student"], (1150,442), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q1a: {str(q1.loc[q1.index[0], 'grade'])}", (1150,517), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q1b: {str(q1.loc[q1.index[1], 'grade'])}", (1150,592), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q1c: {str(q1.loc[q1.index[2], 'grade'])}", (1150,667), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q1d: {str(q1.loc[q1.index[3], 'grade'])}", (1150,742), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, f"Q2a: {str(q2.loc[q1.index[0], 'grade'])}", (1150,817), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q2b: {str(q2.loc[q1.index[1], 'grade'])}", (1150,892), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q2c: {str(q2.loc[q1.index[2], 'grade'])}", (1150,967), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img, f"Q2d: {str(q2.loc[q1.index[3], 'grade'])}", (1150,1042), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = warped_img

def next_submission():
    st.session_state["script_index"] += 1
    del st.session_state["graded_submission"]
    # ==============================
    st.session_state["one_a_lat"] = ""
    st.session_state["one_a_lon"] = ""
    st.session_state["one_b_lat"] = ""
    st.session_state["one_b_lon"] = ""
    st.session_state["one_c_lat"] = ""
    st.session_state["one_c_lon"] = ""
    st.session_state["one_d_lat"] = ""
    st.session_state["one_d_lon"] = ""
    st.session_state["two_a_lat"] = ""
    st.session_state["two_a_lon"] = ""
    st.session_state["two_b_lat"] = ""
    st.session_state["two_b_lon"] = ""
    st.session_state["two_c_lat"] = ""
    st.session_state["two_c_lon"] = ""
    st.session_state["two_d_lat"] = ""
    st.session_state["two_d_lon"] = ""
    st.session_state["one_a_lat_dir"] = None
    st.session_state["one_a_lon_dir"] = None
    st.session_state["one_b_lat_dir"] = None
    st.session_state["one_b_lon_dir"] = None
    st.session_state["one_c_lat_dir"] = None
    st.session_state["one_c_lon_dir"] = None
    st.session_state["one_d_lat_dir"] = None
    st.session_state["one_d_lon_dir"] = None
    st.session_state["two_a_lat_dir"] = None
    st.session_state["two_a_lon_dir"] = None
    st.session_state["two_b_lat_dir"] = None
    st.session_state["two_b_lon_dir"] = None
    st.session_state["two_c_lat_dir"] = None
    st.session_state["two_c_lon_dir"] = None
    st.session_state["two_d_lat_dir"] = None
    st.session_state["two_d_lon_dir"] = None
    
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
    st.header("Practical 1 — Converting Coordinates")

with st.expander("Instructions", expanded = False):
    st.markdown("""
    1. Enter your name in the provided field.
    2. Load the student submission.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided. For DMS, enter data using forward slashes. For example 23°25'36'' becomes 23/25/36.
    7. **DON'T** use commas for decimal marks. Please use a full-stop.
    8. If they didn't add the cardinal direction, select the "Other" option from the drop-down menu.
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
    pin = st.text_input("Enter PIN number",
                        type = "password",
                        key = "user_pin_pa1")
    uploaded_files = st.file_uploader("Select the student submission",
                                      type = ["png"],
                                      accept_multiple_files = True,
                                      key = str(st.session_state["uploader_key"]))
    st.button("Clear", on_click = clear_files)

valid_pin_pa1 = st.secrets.get("secret_pin_pa1")
    
if uploaded_files and grader.strip() and st.session_state["user_pin_pa1"].strip() == valid_pin_pa1:
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

    # display student details
    
    st.markdown(f"""
    - *Name*: **{name}**
    - *Surname*: **{surname}**
    - *Student Number*: **{emplid}**
    """)
    
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

        # get the coordinates of the points to maximise scanned area
        ids = ids.tolist()
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
                                        (2480,3508))

        del cv_img
        gc.collect()

        _, disp_img = cv.imencode(".jpg",warped_img, [int(cv.IMWRITE_JPEG_QUALITY), 80])
        b64_str = base64.b64encode(disp_img).decode("utf-8")
        img_url = f"data:image/png;base64,{b64_str}"


    except:
        st.error("Can't process submission.")

    # display submission and grading tools in two cols
    col1, col2 = st.columns(2)
    
    with col1:    
        submission_viewer(img_url)

    with col2:
        with st.expander("Question 1", expanded=False):
            q1_col1, q1_col2, q1_col3, q1_col4 = st.columns(4)

            with q1_col1:
                st.text_input("(a) — Latitude",  key="one_a_lat")
                st.text_input("(a) — Longitude", key="one_a_lon")
                st.text_input("(b) — Latitude",  key="one_b_lat")
                st.text_input("(b) — Longitude", key="one_b_lon")
                
            with q1_col2:
                st.selectbox("Dir", ("S", "Other"), key="one_a_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("E", "Other"), key="one_a_lon_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("S", "Other"), key="one_b_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("W", "Other"), key="one_b_lon_dir", placeholder = "Make a selection...", index = None)
                
            with q1_col3:
                st.text_input("(c) — Latitude",  key="one_c_lat")
                st.text_input("(c) — Longitude", key="one_c_lon")
                st.text_input("(d) — Latitude",  key="one_d_lat")
                st.text_input("(d) — Longitude", key="one_d_lon")

            with q1_col4:
                st.selectbox("Dir", ("N", "Other"), key="one_c_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("E", "Other"), key="one_c_lon_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("N", "Other"), key="one_d_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("Dir", ("W", "Other"), key="one_d_lon_dir", placeholder = "Make a selection...", index = None)

            pass

        with st.expander("Question 2", expanded=False):
            q2_col1, q2_col2, q2_col3, q2_col4 = st.columns(4)

            with q2_col1:
                st.text_input("2(a) — Latitude",  key = "two_a_lat")
                st.text_input("2(a) — Longitude", key = "two_a_lon")
                st.text_input("2(b) — Latitude",  key = "two_b_lat")
                st.text_input("2(b) — Longitude", key = "two_b_lon")

            with q2_col2:
                st.selectbox("2(a) — Latitude (Dir)",  ("S", "Other"), key = "two_a_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(a) — Longitude (Dir)", ("E", "Other"), key = "two_a_lon_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(b) — Latitude (Dir)",  ("S", "Other"), key = "two_b_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(b) — Longitude (Dir)", ("W", "Other"), key = "two_b_lon_dir", placeholder = "Make a selection...", index = None)

            with q2_col3:
                st.text_input("2(c) — Latitude",  key = "two_c_lat")
                st.text_input("2(c) — Longitude", key = "two_c_lon")
                st.text_input("2(d) — Latitude",  key = "two_d_lat")
                st.text_input("2(d) — Longitude", key = "two_d_lon")

            with q2_col4:
                st.selectbox("2(c) — Latitude (Dir)",  ("N", "Other"), key = "two_c_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(c) — Longitude (Dir)", ("E", "Other"), key = "two_c_lon_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(d) — Latitude (Dir)",  ("N", "Other"), key = "two_d_lat_dir", placeholder = "Make a selection...", index = None)
                st.selectbox("2(d) — Longitude (Dir)", ("W", "Other"), key = "two_d_lon_dir", placeholder = "Make a selection...", index = None)
                    
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
            meta_info.add_text("q1", st.session_state["q1"])
            meta_info.add_text("q2", st.session_state["q2"])
            meta_info.add_text("final", st.session_state["final"])
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)
            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
