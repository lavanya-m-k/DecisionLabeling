import os

# ROOT_DIR = '/'.join(os.getcwd().split('/')[:-1])#""
ROOT_DIR = ""
STATE_PATH = os.path.join(ROOT_DIR, "state.pkl")
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
RESOURCES_DIR = os.path.join(ROOT_DIR, "res")
SERVER_DIR = "UltimateLabeling_server/"

COLUMN_NAMES = ["track_id", "class_id", "x", "y", "w", "h", "polygon",
 "kp", "tagged_frame", "total_frames"]