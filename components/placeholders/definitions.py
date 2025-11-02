# ====================================================
# General placeholders
# ====================================================
PLACEHOLDER_INPUTFILE_FOLDER = "{inputfile_folder}"
PLACEHOLDER_INPUTFILE_NAME = "{inputfile_name}"
PLACEHOLDER_INPUTFILE_EXT = "{inputfile_ext}"
PLACEHOLDER_OUTPUT_FOLDER = "{output_folder}"

GENERAL_PLACEHOLDERS = [
    PLACEHOLDER_INPUTFILE_FOLDER,
    PLACEHOLDER_INPUTFILE_NAME,
    PLACEHOLDER_INPUTFILE_EXT,
    PLACEHOLDER_OUTPUT_FOLDER,
]

# ====================================================
# Video Cutter Specific Placeholders
# ====================================================
PLACEHOLDER_START_TIME = "{start_time}"
PLACEHOLDER_END_TIME = "{end_time}"
PLACEHOLDER_SAFE_START_TIME = "{safe_start_time}"
PLACEHOLDER_SAFE_END_TIME = "{safe_end_time}"

VIDEO_CUTTER_PLACEHOLDERS = [
    PLACEHOLDER_INPUTFILE_FOLDER,
    PLACEHOLDER_INPUTFILE_NAME,
    PLACEHOLDER_INPUTFILE_EXT,
    PLACEHOLDER_START_TIME,
    PLACEHOLDER_END_TIME,
    PLACEHOLDER_OUTPUT_FOLDER,
    PLACEHOLDER_SAFE_START_TIME,
    PLACEHOLDER_SAFE_END_TIME,
]

# ====================================================
# Video Joiner Specific Placeholders
# ====================================================
PLACEHOLDER_CONCATFILE_PATH = "{concatfile_path}"

VIDEO_JOINER_PLACEHOLDERS = [
    PLACEHOLDER_INPUTFILE_FOLDER,
    PLACEHOLDER_OUTPUT_FOLDER,
    PLACEHOLDER_CONCATFILE_PATH
]