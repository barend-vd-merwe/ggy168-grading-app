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
import gc

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
    edited_df["length"] = pd.to_numeric(edited_df["length"])
    edited_df["width"] = pd.to_numeric(edited_df["width"])
    edited_df["area"] = pd.to_numeric(edited_df["area"])
    
    memo_dict = {
        "s" : [1,2,3,4],
        "l" : [memo["strip1"]["length"]["ans"],
               memo["strip2"]["length"]["ans"],
               memo["strip3"]["length"]["ans"],
               memo["strip4"]["length"]["ans"]],
        "l_fc" : [memo["strip1"]["length"]["fc"],
                  memo["strip2"]["length"]["fc"],
                  memo["strip3"]["length"]["fc"],
                  memo["strip4"]["length"]["fc"]],
        "l_pc" : [memo["strip1"]["length"]["pc"],
                  memo["strip2"]["length"]["pc"],
                  memo["strip3"]["length"]["pc"],
                  memo["strip4"]["length"]["pc"]],
        "l_sub" : [edited_df.loc[edited_df["strip"] == 1, "length"].item(),
                   edited_df.loc[edited_df["strip"] == 2, "length"].item(),
                   edited_df.loc[edited_df["strip"] == 3, "length"].item(),
                   edited_df.loc[edited_df["strip"] == 4, "length"].item()],
        "w" : [memo["strip1"]["width"]["ans"],
               memo["strip2"]["width"]["ans"],
               memo["strip3"]["width"]["ans"],
               memo["strip4"]["width"]["ans"]],
        "w_fc" : [memo["strip1"]["width"]["fc"],
                  memo["strip2"]["width"]["fc"],
                  memo["strip3"]["width"]["fc"],
                  memo["strip4"]["width"]["fc"]],
        "w_pc" : [memo["strip1"]["width"]["pc"],
                  memo["strip2"]["width"]["pc"],
                  memo["strip3"]["width"]["pc"],
                  memo["strip4"]["width"]["pc"]],
        "w_sub" : [edited_df.loc[edited_df["strip"] == 1, "width"].item(),
                   edited_df.loc[edited_df["strip"] == 2, "width"].item(),
                   edited_df.loc[edited_df["strip"] == 3, "width"].item(),
                   edited_df.loc[edited_df["strip"] == 4, "width"].item()],
        "a" : [memo["strip1"]["area"]["ans"],
               memo["strip2"]["area"]["ans"],
               memo["strip3"]["area"]["ans"],
               memo["strip4"]["area"]["ans"]],
        "a_fc" : [memo["strip1"]["area"]["fc"],
                  memo["strip2"]["area"]["fc"],
                  memo["strip3"]["area"]["fc"],
                  memo["strip4"]["area"]["fc"]],
        "a_pc" : [memo["strip1"]["area"]["pc"],
                  memo["strip2"]["area"]["pc"],
                  memo["strip3"]["area"]["pc"],
                  memo["strip4"]["area"]["pc"]],
        "a_sub" : [edited_df.loc[edited_df["strip"] == 1, "area"].item(),
                   edited_df.loc[edited_df["strip"] == 2, "area"].item(),
                   edited_df.loc[edited_df["strip"] == 3, "area"].item(),
                   edited_df.loc[edited_df["strip"] == 4, "area"].item()],
        "grade" : [0.0,0.0,0.0,0.0]
    }

    df = pd.DataFrame(memo_dict)

    length_fc = df["l_sub"].between(df["l"] - df["l_fc"],
                                    df["l"] + df["l_fc"])
    length_pc = df["l_sub"].between(df["l"] - df["l_pc"],
                                    df["l"] + df["l_pc"])
    length_opt = [length_fc, length_pc]
    length_grd = [1.0, 0.5]
    df["grade"] += np.select(length_opt, length_grd, default = 0.0)

    width_fc = df["w_sub"].between(df["w"] - df["w_fc"],
                                   df["w"] + df["w_fc"])
    width_pc = df["w_sub"].between(df["w"] - df["w_pc"],
                                   df["w"] + df["w_pc"])
    width_opt = [width_fc, width_pc]
    width_grd = [1.0, 0.5]
    df["grade"] += np.select(width_opt, width_grd, default = 0.0)

    area_fc = df["a_sub"].between(df["a"] - df["a_fc"],
                                  df["a"] + df["a_fc"])
    area_pc = df["a_sub"].between(df["a"] - df["a_pc"],
                                  df["a"] + df["a_pc"])
    area_opt = [area_fc, area_pc]
    area_grd = [1.0, 0.5]
    df["grade"] += np.select(area_opt, area_grd, default = 0.0)

    tbl_grd = df["grade"].sum()

    ta = memo["total"]["ans"]
    ta_fc = memo["total"]["fc"]
    ta_pc = memo["total"]["pc"]
    ta_sub = float(st.session_state["sub_ta"])
    ta_sub_unt = st.session_state["sub_ta_unt"]

    ta_range = [
        (ta - ta_fc, ta + ta_fc, 1.0),
        (ta - ta_pc, ta + ta_pc, 0.5)
    ]

    ta_grd = 0.0
    ta_grd += next((grade for lower, upper, grade in ta_range if lower <= ta_sub <= upper),0)
    ta_grd += float(ta_sub_unt == "Full Credit")

    wrk_grd = 0.0
    for work in ["wrk_strip1","wrk_strip2","wrk_strip3","wrk_strip4"]:
        if st.session_state[work] == "Full Credit":
            wrk_grd += 2.0
        elif st.session_state[work] == "Partial Credit":
            wrk_grd += 1.0
        else:
            wrk_grd += 0.0

    st.session_state["tbl_grd"] = tbl_grd
    st.session_state["ta_grd"] = ta_grd
    st.session_state["wrk_grd"] = wrk_grd
    st.session_state["final_grade"] = tbl_grd + ta_grd + wrk_grd

    conn = st.connection("gsheets", type=GSheetsConnection)
    gc = conn.read(ttl=0)
    column_name = "Practical assignment 5 [Total Pts: 13 Score] |2934611"
    gc.loc[gc["Username"] == emplid, column_name] = st.session_state["final_grade"]
    conn.update(data=gc)
    
    cv.putText(warped_img,str(df.iloc[df["s"] == 1, 13].item()),(2325,645), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img,str(df.iloc[df["s"] == 2, 13].item()),(2325,714), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img,str(df.iloc[df["s"] == 3, 13].item()),(2325,783), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img,str(df.iloc[df["s"] == 4, 13].item()),(2325,845), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img,str(ta_grd),(2325,1083), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)
    cv.putText(warped_img,str(wrk_grd),(1869,1608), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    cv.putText(warped_img, str(st.session_state["final_grade"]), (850,455), cv.FONT_HERSHEY_SIMPLEX, 3.0, (0,0,255), 1)
    cv.putText(warped_img, st.session_state["student"], (303,199), cv.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 1)

    st.session_state["graded_submission"] = warped_img
    
    

def next_submission():
    st.session_state["script_index"] += 1
    st.session_state["editor_version"] += 1
    del st.session_state["graded_submission"]
    gc.collect()
    # ==============================
    edited_df.iloc[:, 1:3] = None
    st.session_state["sub_ta"] = ""
    st.session_state["sub_ta_unt"] = None
    st.session_state["wrk_strip1"] = None
    st.session_state["wrk_strip2"] = None
    st.session_state["wrk_strip3"] = None
    st.session_state["wrk_strip4"] = None
    
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
    st.image("NAS_Faculty Logo.jpg")

with title_col2:
    st.title("GGY 168 — Introduction to Physical Geography")
    st.header("Practical 5 — Area")

with st.expander("Instructions", expanded = False):
    st.markdown("""
    1. Enter your name in the provided space.
    2. Load the student submission.
    3. If there is an error during loading, refresh your browser window and try again.
    4. If it still doesn't work, send me an email with the student's details and move on to the next submission.
    5. Verify that the name on the submission matches the name of the file.
    6. Transfer the answers on the submission to the spaces provided.
    7. If the student appears to numbered their strips from the bottom up, fill in the values accordingly. In other words, the values for "Strip 1" must be the most notherly part of the feature being measured. So if the student started at the bottom, their strip 4 would represent the most northerly part of the feature. Hence, you would enter those values into the first row of the table. I have provided the memo table as a reference to help you orientate yourself.
    8. For the work shown, I leave it at your discretion. If you are satisfied that you can see the student actually worked on the map, you can award "Full Credit". Otherwise (i.e. there is no evidence of any work being done in the plot area), you should award "No Credit".
    9. **DON'T** use commas for decimal marks. Please use a full-stop.
    10. When you are done, press the grade button.
    11. Download the graded submission and store it in a separate folder. **DON'T** change the filename.
    """)

if "script_index" not in st.session_state:
    st.session_state["script_index"] = 0

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 100

if "editor_version" not in st.session_state:
    st.session_state["editor_version"] = 200

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

with open ("memo.yaml", "r", encoding = "utf-8") as file:
        memo = yaml.safe_load(file)

valid_pin = st.secrets.get("secret_pin")
        
if uploaded_files and grader.strip() and st.session_state["user_pin"].strip() == valid_pin:
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

        ac = pd.read_csv("aruco.csv")

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

        with st.expander("Example table", expanded = False):
            eg_tbl = {
                "Strip" : [1,2,3,4],
                "Length" : [memo["strip1"]["length"]["ans"],
                            memo["strip2"]["length"]["ans"],
                            memo["strip3"]["length"]["ans"],
                            memo["strip4"]["length"]["ans"]],
                "Width" : [memo["strip1"]["width"]["ans"],
                           memo["strip2"]["width"]["ans"],
                           memo["strip3"]["width"]["ans"],
                           memo["strip4"]["width"]["ans"]],
                "Area" : [memo["strip1"]["area"]["ans"],
                          memo["strip2"]["area"]["ans"],
                          memo["strip3"]["area"]["ans"],
                          memo["strip4"]["area"]["ans"]]
            }

            eg_tbl = pd.DataFrame(eg_tbl)

            st.dataframe(eg_tbl,
                         width="stretch",
                         hide_index = True)

        raw_table = [
            {"strip": 1, "length": None, "width": None, "area": None},
            {"strip": 2, "length": None, "width": None, "area": None},
            {"strip": 3, "length": None, "width": None, "area": None},
            {"strip": 4, "length": None, "width": None, "area": None}
        ]

        sub_df = pd.DataFrame(raw_table)

        edited_df = st.data_editor(
            sub_df,
            column_config = {
                "strip": st.column_config.NumberColumn(
                    "Strip",
                    disabled = True
                ),
                "length": st.column_config.NumberColumn(
                    "Length (km)",
                    disabled = False,
                    required = True
                ),
                "width": st.column_config.NumberColumn(
                    "Width (km)",
                    disabled = False,
                    required = True
                ),
                "area": st.column_config.NumberColumn(
                    "Area (km²)",
                    disabled = False,
                    required = True
                )
            },
            hide_index = True,
            width = "stretch",
            key = str(st.session_state["editor_version"])
        )

        tot_col1, tot_col2 = st.columns(2)

        with tot_col1:
            st.text_input("Total Area", key = "sub_ta")

        with tot_col2:
            st.selectbox("Units (km²)",
                         ("Full Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "sub_ta_unt")

        st.markdown("**Work Shown**")
        wrk_col1, wrk_col2, wrk_col3, wrk_col4 = st.columns(4)

        with wrk_col1:
            st.selectbox("Strip 1",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "wrk_strip1")
        with wrk_col2:
            st.selectbox("Strip 2",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "wrk_strip2")

        with wrk_col3:
            st.selectbox("Strip 3",
                         ("Full Credit", "Partial Credit", "No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "wrk_strip3")

        with wrk_col4:
            st.selectbox("Strip 4",
                         ("Full Credit", "Partial Credit","No Credit"),
                         index = None,
                         placeholder = "Make a selection...",
                         key = "wrk_strip4")
            
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
            meta_info.add_text("Table", str(st.session_state["tbl_grd"]))
            meta_info.add_text("Total Area", str(st.session_state["ta_grd"]))  
            meta_info.add_text("Work", str(st.session_state["wrk_grd"]))
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG", pnginfo=meta_info)

            with button_col2:
                st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

            if st.session_state["script_index"] < len(uploaded_files) - 1:
                with button_col3:
                    st.button("Next Submission", on_click = next_submission)
