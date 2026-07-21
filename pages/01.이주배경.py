import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

APP_TITLE = "국내 체류 외국인 신규 유입·유출 통계"

FILE_NAME = "국내 체류 외국인 신규 유입·유출 통계(2026년 6월).xlsx"

DATA_PATH = Path(FILE_NAME)

PAGE_ICON = "🌏"

LAYOUT = "wide"

PRIMARY_COLOR = "#2E86DE"

MONTHS = [
    "2월",
    "3월",
    "4월",
    "5월",
    "6월"
]

KEYWORDS = {
    "유입":["유입","입국"],
    "유출":["유출","출국"],
    "순증감":["순증","증감"]
}
# config.py

from pathlib import Path

APP_TITLE = "국내 체류 외국인 신규 유입·유출 통계"

FILE_NAME = "국내 체류 외국인 신규 유입·유출 통계(2026년 6월).xlsx"

DATA_PATH = Path(FILE_NAME)

PAGE_ICON = "🌏"

LAYOUT = "wide"

PRIMARY_COLOR = "#2E86DE"

MONTHS = [
    "2월",
    "3월",
    "4월",
    "5월",
    "6월"
]

KEYWORDS = {
    "유입":["유입","입국"],
    "유출":["유출","출국"],
    "순증감":["순증","증감"]
}
import pandas as pd

from config import DATA_PATH
from config import KEYWORDS

from functools import lru_cache


@lru_cache(maxsize=1)
def load_workbook():

    sheets = pd.read_excel(
        DATA_PATH,
        sheet_name=None,
        engine="openpyxl"
    )

    return sheets


def find_sheet(keyword):

    sheets = load_workbook()

    for sheet in sheets.keys():

        lower = sheet.replace(" ","")

        for k in KEYWORDS[keyword]:

            if k in lower:

                return sheet

    return list(sheets.keys())[0]


def get_dataframe(keyword):

    sheet = find_sheet(keyword)

    df = load_workbook()[sheet]

    return df.copy()


def clean_dataframe(df):

    df = df.copy()

    df.columns = [
        str(c).replace("\n","").strip()
        for c in df.columns
    ]

    df = df.dropna(how="all")

    df = df.reset_index(drop=True)

    return df


def numeric_columns(df):

    cols = []

    for c in df.columns:

        try:

            pd.to_numeric(
                df[c]
                .astype(str)
                .str.replace(",",""),
                errors="raise"
            )

            cols.append(c)

        except:

            pass

    return cols


def convert_numeric(df):

    df = df.copy()

    for c in numeric_columns(df):

        df[c] = (
            df[c]
            .astype(str)
            .str.replace(",","")
        )

        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    return df


def detect_region_column(df):

    names = [
        "지역",
        "시도",
        "지역명",
        "행정구역",
        "광역"
    ]

    for c in df.columns:

        for n in names:

            if n in c:

                return c

    return df.columns[0]


def region_list(df):

    col = detect_region_column(df)

    return sorted(
        df[col]
        .dropna()
        .astype(str)
        .unique()
    )


def filter_region(df, region):

    col = detect_region_column(df)

    return df[df[col]==region]
    
