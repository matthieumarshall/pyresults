GUESTS = ["1635", "1636", "956", "1652"] + [str(x) for x in range(1718, 1764)]

CATEGORIES = ["U9B", "U9G", "U11B", "U11G", "U13B", "U13G", "U15B", "U15G", "U17M"] + \
    ["U17W", "U20M", "U20W", "SW", "SM"] + \
    ["WV40", "MV40", "WV50", "MV50", "WV60", "MV60", "WV70", "MV70"]

MENS_DIVISIONS = {
    "Abingdon AC A": "1",
    "Swindon Harriers A": "1",
    "Oxford City AC A": "1",
    "Headington RR A": "1",
    "Witney Road Runners A": "1",
    "Newbury AC A": "1",
    "White Horse Harriers A": "1",
    "Alchester Running Club A": "1",
    "Didcot Runners A": "1",
    "Swindon Harriers B": "1",
    "Abingdon AC B": "2",
    "Witney Road Runners B": "2",
    "Newbury AC B": "2",
    "Headington RR B": "2",
    "Woodstock Harriers AC A": "2",
    "Eynsham Road Runners A": "2",
    "Harwell Harriers A": "2",
    "White Horse Harriers B": "2",
    "Oxford Tri A": "2",
    "Radley Athletic Club A": "2",
    # everyone else is in division 3
}

WOMENS_DIVISIONS = {
    "Headington RR A": "1",
    "Oxford City AC A": "1",
    "Swindon Harriers A": "1",
    "Abingdon AC A": "1",
    "Newbury AC A": "1",
    "Headington RR B": "1",
    "White Horse Harriers A": "1",
    "Witney Road Runners A": "1",
    "Headington RR C": "1",
    "Didcot Runners A": "1",
    "Banbury harriers AC A": "2",
    "Highworth RC A": "2",
    "Radley Athletic Club A": "2",
    "Eynsham Road Runners A": "2",
    "Woodstock Harriers AC A": "2",
    "Hook Norton Harriers A": "2",
    "Oxford Tri A": "2",
    "Bicester AC A": "2",
    "Newbury AC B": "2",
    "Alchester Running Club A": "2",
    # everyone else is in division 3
}

GENDER_MAPPINGS = {
    "Men": "Male",
    "U11B": "Male",
    "U11G": "Female",
    "Women": "Female"
}

CATEGORY_MAPPINGS = {
    ("Male", "Senior Men"): "SM",
    ("Male", "U20 Men"): "U20M",
    ("Male", "V40"): "MV40",
    ("Male", "V50"): "MV50",
    ("Male", "V60"): "MV60",
    ("Male", "V70+"): "MV70",
    ("Female", "Senior Women"): "SW",
    ("Female", "U20 Women"): "U20W",
    ("Female", "V40"): "WV40",
    ("Female", "V50"): "WV50",
    ("Female", "V60"): "WV60",
    ("Female", "V70+"): "WV70",
    ("Male", "U9 Boys"): "U9B",
    ("Female", "U9 Girls"): "U9G",
    ("Male", "U11 Boys"): "U11B",
    ("Female", "U11 Girls"): "U11G",
    ("Male", "U13 Boys"): "U13B",
    ("Female", "U13 Girls"): "U13G",
    ("Male", "U15 Boys"): "U15B",
    ("Female", "U15 Girls"): "U15G",
    ("Male", "U17 Boys"): "U17M",
    ("Female", "U17 Girls"): "U17W",
}

RACE_MAPPINGS = {
    "U9B": "U9",
    "U9G": "U9",
    "U11B": "U11B",
    "U11G": "U11G",
    "U13B": "U13",
    "U13G": "U13",
    "U15B": "U15",
    "U15G": "U15",
    "U17M": "U17",
    "U17W": "U17",
    "U20M": "Men",
    "U20W": "Women",
    "SW": "Women",
    "SM": "Men",
    "WV40": "Women",
    "MV40": "Men",
    "WV50": "Women",
    "MV50": "Men",
    "WV60": "Women",
    "MV60": "Men",
    "WV70": "Women",
    "MV70": "Men"
}