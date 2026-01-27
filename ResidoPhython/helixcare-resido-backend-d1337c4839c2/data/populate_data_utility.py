import random
import re
import string

from django.contrib.gis.geos import GEOSGeometry
from faker import Faker

fake = Faker()

qualification_list = [
    "BCh",
    "BM",
    "BMedSci",
    "BPharm",
    "BS",
    "BSc",
    "DA",
    "DCh",
    "DCPath",
    "DGO",
    "DMR",
    "DPath",
    "DPhil",
    "DPhysMed",
    "DPH",
    "DRCPath",
    "DS",
    "FFPath",
    "FRCA",
    "FRCGP",
    "FRCPath",
    "FRCS",
    "GP",
    "MA",
    "MBAcA",
    "MBBCh",
    "MBBS",
    "MBChB",
    "MCh",
    "MChOrth",
    "MClinPscychol",
    "MD",
    "MMed",
    "MMedSc",
    "MPhil",
    "MRCPath",
    "MRCPsych",
    "MRCS",
    "MS",
    "MSc",
    "PhD",
    "SHO",
    "SpR",
]


def generate_random_middle_name():
    middle_name_length = random.randint(1, 3)
    middle_name = "".join(
        random.choice(string.ascii_letters) for _ in range(middle_name_length)
    )
    return middle_name


def get_lat_long_point():
    latitude = random.uniform(25, 45)
    longitude = random.uniform(85, 150)

    latlng_tuple = (latitude, longitude)
    latlng = GEOSGeometry(
        "POINT(" + str(latlng_tuple[0]) + " " + str(latlng_tuple[1]) + ")", srid=4326
    )
    return latlng


def standardize_medical_degree(input_string):
    print("Input string: ", input_string)
    if input_string:
        cleaned_string = re.sub(r"[^a-zA-Z0-9.-]", "", input_string)
        print("Cleaned string: ", cleaned_string)
        cleaned_string = re.sub(r"[.-](?=[a-zA-Z])", "", cleaned_string)
        print("Final string: ", cleaned_string)
    else:
        cleaned_string = input_string
    return cleaned_string
