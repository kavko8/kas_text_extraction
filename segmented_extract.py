import collections
import re
import subprocess
#from difflib import SequenceMatcher
import os
from natsort import natsorted
from polyglot.detect import Detector
from polyglot.detect.base import logger as polyglot_logger
import tqdm
from pdf2image import convert_from_path
import numpy as np
import cv2
import json
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher

polyglot_logger.setLevel("ERROR")


PATTERNS = {
    "slika": [f"slika{i}:" for i in range(200)],
    "slika2": [f"slika{i}." for i in range(200)],
    "tabela": [f"tabela{i}:" for i in range(200)],
    "tabela2": [f"tabela{i}." for i in range(200)],
    "preglednica": [f"preglednica{i}:" for i in range(200)],
    "preglednica2": [f"preglednica{i}." for i in range(200)],
    "grafikon": [f"grafikon{i}:" for i in range(200)],
    "grafikon2": [f"grafikon{i}." for i in range(200)],
    "graf": [f"graf{i}:" for i in range(200)],
    "graf2": [f"graf{i}." for i in range(200)],
    "vir": ["vir:", "(vir:", "viri:"],
    "prikazi": [f"prikaz{i}:." for i in range(300)],
}

def remove_noise(txt, figs=False):
    txt = re.sub('[\u000B\u000C\u000D\u0085\u2028\u2029]+', '', txt)
    txt = re.sub(" +", " ", txt)
    txt = txt.replace("\uf0b7", "-")
    txt = txt.replace("•", "-")
    txt = txt.replace("ţ", "ž")
    txt = txt.replace("Ţ", "Ž")
    txt = txt.replace("Ċ", "Č")
    txt = txt.replace("ċ", "č")
    txt = txt.replace("", "")
    txt = txt.replace("\t", "")
    txt = txt.replace("\u000C", "")
    txt = txt.replace("", "")
    txt = txt.split("\n")
    indexes_to_remove = []
    if figs:
        for idx, line in enumerate(txt):
            check_second = False
            if len(line) > 1:
                no_spaces = line.replace(" ", "")

                if len(no_spaces):
                    if len(no_spaces) < 4 and not no_spaces[-1] in [".", ",", "!", "?", ":", ";"]:
                        indexes_to_remove.append(idx)
                    if line.count(" ") > len(no_spaces) and not no_spaces[-1] in [".", ",", "!", "?", ":", ";"]:
                        indexes_to_remove.append(idx)
                    if no_spaces[:7].lower() in PATTERNS["slika"] or no_spaces[:8].lower() in PATTERNS["slika"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:8].lower() in PATTERNS["tabela"] or no_spaces[:9].lower() in PATTERNS["tabela"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:6].lower() in PATTERNS["graf"] or no_spaces[:7].lower() in PATTERNS["graf"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:13].lower() in PATTERNS["preglednica"] or no_spaces[:14].lower() in PATTERNS[
                        "preglednica"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:13].lower() in PATTERNS["grafikon"] or no_spaces[:14].lower() in PATTERNS[
                        "grafikon"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:7].lower() in PATTERNS["slika2"] or no_spaces[:8].lower() in PATTERNS["slika2"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:8].lower() in PATTERNS["tabela2"] or no_spaces[:9].lower() in PATTERNS["tabela2"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:6].lower() in PATTERNS["graf2"] or no_spaces[:7].lower() in PATTERNS["graf2"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:13].lower() in PATTERNS["preglednica2"] or no_spaces[:14].lower() in PATTERNS[
                        "preglednica2"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:13].lower() in PATTERNS["grafikon2"] or no_spaces[:14].lower() in PATTERNS[
                        "grafikon2"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:4].lower() in PATTERNS["vir"] or no_spaces[:5] in PATTERNS["vir"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if no_spaces[:8].lower() in PATTERNS["prikazi"] or no_spaces[:9] in PATTERNS["prikazi"] or no_spaces[
                                                                                                               :10] in \
                            PATTERNS["prikazi"]:
                        indexes_to_remove.append(idx)
                        check_second = True
                    if check_second:
                        try:
                            if txt[idx + 1].islower() and len(txt[idx + 1]) < len(line) and txt[idx + 1][-1] not in [".",
                                                                                                                     ",",
                                                                                                                     "!",
                                                                                                                     "?",
                                                                                                                     ":",
                                                                                                                     ";"]:
                                indexes_to_remove.append(idx + 1)
                        except IndexError:
                            pass
                    if sum([len(i) for i in line.split(" ")]) / len([i for i in line.split(" ") if len(i)]) < 2.5:
                        indexes_to_remove.append(idx)
            #else:
            #    indexes_to_remove.append(idx)

    new_txt = "\n".join([i for idx, i in enumerate(txt) if idx not in indexes_to_remove])
    return new_txt


toc_idx = {
    "kazalo": ["kazalo", "vsebina", "kazalo vsebine"],
    "kljucne": ["ključne besede", "kljucne besede", "ključne", "kljucne", "ključni"],
    "povzetek": ["povzetek", "izvlecek", "izvleček"],
    "ostala kazala": ["kazalo slik", "seznam slik", "kazalo tabel", "seznam tabel"],
    "abstracts": ["abstract", "summary"],
    "besede": ["besede", "besede:", "pojmi"]
}


def similar(a: str, b: str, conf: float = 0.6):
    ratio = SequenceMatcher(None, a, b).ratio()
    similarity = True if ratio >= conf else False
    return similarity


def check_language(text: str, lang: str = "sl", conf: int = 70):
    l = False
    language = Detector(text, quiet=True)
    if language.languages[0].code == lang:  # check  the first language (highest percentage) of the output
        if int(language.languages[0].confidence) > conf:
            l = True
    return l


def get_end_index(pdf_name, index, offset, bottom):
    found_end = False
    images = convert_from_path(pdf_name, dpi=72)  # , last_page=15)
    img = np.array(images[index])
    img = img[offset:bottom, 0:img.shape[1]]
    line = img.shape[0]
    gray = gray_img(img)
    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)
    kernel = np.ones((5, img.shape[1]), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cnts = search_contours(thresh)
    cnts.sort(key=lambda c: cv2.boundingRect(c)[1])
    for cnt in reversed(cnts):
        x, y, w, h = cv2.boundingRect(cnt)
        if w < img.shape[1]//2:
            found_end = True
            line = y-1
    try:
        cv2.imshow("thr_crop", thresh)# np.array(images[9])[offset:bottom, 0:img.shape[1]])
        cv2.imshow("crop", img[offset:line, 0:img.shape[1]])
        cv2.imshow("img", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        pass
    return found_end, line




def calculate_crop_area(pdf_name, index):



    images = convert_from_path(pdf_name, dpi=72)  # , last_page=15)
    img = np.array(images[index])

    offset = 0
    bottom = img.shape[0]

    '''
    gray = gray_img(img)
    thresh = otsu_img(gray)
    
    
    if is_white(thresh):
        thresh = invert_img(thresh)
    kernel = np.ones((20, img.shape[1]), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cnts = search_contours(thresh)
    cnts = [c for c in cnts if cv2.boundingRect(c)[2] > 60*img.shape[1]//100 and cv2.boundingRect(c)[3] > 20]
    cnts.sort(key=lambda c: cv2.boundingRect(c)[1], reverse=False)
    #cnt = max(cnts, key=lambda c: cv2.contourArea(c))
    cnt = cnts[0]
    _, sY, _, _ = cv2.boundingRect(cnt)
    max_top = sY
    '''
    max_top = 250
    gray = gray_img(img)
    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)[0:max_top, 0:img.shape[1]]
    else:
        thresh = thresh[0:max_top, 0:img.shape[1]]

    kernel = np.ones((1, 15), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    cnts = search_contours(thresh)
    if len(cnts):
        cnts.sort(key=lambda c: cv2.boundingRect(c)[2])
        cnt = cnts[-1]
        x, y, width, height = cv2.boundingRect(cnt)
        if width > img.shape[1]//5 and height < 3:
            offset = y + height


    max_top = 115
    if not offset:
        thresh = otsu_img(gray)
        if is_white(thresh):
            thresh = invert_img(thresh)[0:max_top, 0:img.shape[1]]
        else:
            thresh = thresh[0:max_top, 0:img.shape[1]]

        kernel = np.ones((15, 25), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((2, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        cnts = search_contours(thresh)
        if len(cnts):
            cnts.sort(key=lambda c: cv2.boundingRect(c)[1], reverse=True)
            for cnt in cnts:
                x, y, width, height = cv2.boundingRect(cnt)
                if abs(width - height) < 30 and 20 > height > 2:
                    offset = y + height
                    break

    '''
    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)

    kernel = np.ones((20, img.shape[1]), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cnts = search_contours(thresh)
    cnts = [c for c in cnts if cv2.boundingRect(c)[2] > 60*img.shape[1]//100 and cv2.boundingRect(c)[3] > 20]
    cnts.sort(key=lambda c: cv2.boundingRect(c)[1], reverse=True)
    cnt = cnts[0]
    #cnt = max(cnts, key=lambda c: cv2.contourArea(c))
    _, sY, _, sH = cv2.boundingRect(cnt)
    max_bottom = img.shape[0] - (sY + sH)
    '''
    max_bottom = 200
    gray = gray_img(img)
    thresh = otsu_img(gray)
    if is_white(thresh):
        thresh = invert_img(thresh)[img.shape[0]-max_bottom:img.shape[0], 0:img.shape[1]]
    else:
        thresh = thresh[img.shape[0]-max_bottom:img.shape[0], 0:img.shape[1]]
    kernel = np.ones((1, 15), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    cnts = search_contours(thresh)
    if len(cnts):
        cnts.sort(key=lambda c: cv2.boundingRect(c)[2])
        cnt = cnts[-1]
        x, y, width, height = cv2.boundingRect(cnt)
        if width > img.shape[1]//5 and height < 3:
            bottom = img.shape[0] - max_bottom + y - 1

    return offset, bottom


def invert_img(img):
    return cv2.bitwise_not(img)


def gray_img(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def otsu_img(gray):
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]


def search_contours(thresh):
    return cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]


def is_white(img):
    return True if np.sum(img == 255) > np.sum(img == 0) else False



def get_abs_index(pdf_name):

    pdf = subprocess.check_output(
        f'pdftotext -layout -enc "UTF-8" -q {pdf_name} -',
        shell=True,
        encoding="UTF-8")
    pdf = pdf.split("\f")
    abs_index = len(pdf)//2
    found_abs = False
    for index, page in enumerate(pdf):
        lines = page.split("\n")
        for line_index, line in enumerate(lines):
            # if index > 5 and pdf_name == "/home/matic/Desktop/pdfji2/kas-7791.pdf":
            #    neki = "hdh
            while line.startswith(" "):
                line = line[1:]
            while line.endswith(" "):
                line = line[:-1]
            if len(line) < 20:
                # if line.count(".") < 3 and line.count("_") < 3 and line.count(" ") < 5 and len(line) < 20:
                first_word = re.sub(r"\d", "", line)
                first_word = first_word.replace(".", "")

                words = first_word.split(" ")

                if len([words]) < 3:
                    if not found_abs:
                        if sum([len(s.replace(" ", "")) for s in lines[line_index:]]) > 200:
                            for w in words:
                                if len(w):
                                    first_word = w.replace(" ", "").lower()
                                    for mark in toc_idx["kazalo"]:
                                        if not first_word.isdigit():
                                            similarity = similar(first_word, mark, conf=0.85)
                                            if similarity:
                                                found_abs = True
                                                abs_index = line_index
                                                break
                                if found_abs:
                                    break
                    else:
                        break
            if found_abs:
                break
        if found_abs:
            break
    return abs_index


# Load your PDF


# If it's password-protected
#with open("secure.pdf", "rb") as f:
#    pdf = pdftotext.PDF(f, "secret")

# How many pages?
#print(len(pdf))

# Iterate over all the pages
#for page in pdf:
#    print(page)

# Read some individual pages
#print(pdf[0])
#print(pdf[1])

# Read all the text into one string
#print("\n\n".join(pdf))
base_name = "/media/matic/My Passport/kas_new_text"
os.makedirs("/media/matic/My Passport/kas_segmented", exist_ok=True)
import pandas as pd
meta = pd.read_table(f"./kas-meta.tbl", sep="\t")  # dataframe of KAS_no_abs metadata
titles = meta["title"].tolist()
titles = [t.lower() for t in titles]

sum_count = tqdm.tqdm(total=len(os.listdir(base_name)))


def main_loop(j, name, base_name, s_c):

    pdf_name = os.path.join(base_name, name)
    # with open(pdf_name, "rb") as f:
    #    pdf = pdftotext.PDF(f)
    title = meta.loc[meta["id"] == name.replace(".txt", "")]["title"].tolist()
    if len(title):
        title = title[0]
    else:
        title = "UNKNOWNUNKNOWNUNKNOWN"
    #get_index = get_abs_index(pdf_name)
    #offset, bottom = calculate_crop_area(pdf_name, get_index)
    #pname = pdf_name.replace("/My Passport", "/My\ Passport")
    #pdf = subprocess.check_output(
    #    f'pdftotext -layout -enc "UTF-8" -r 144 -q {pname} -',  # -y {offset} -H {bottom} -r 72
    #    shell=True,
    #    encoding="UTF-8")  # 82
    pdf = open(pdf_name, "r", encoding="utf-8").read()
    pdf = pdf.split("\f")

    toc_index = -1
    toc_line_index = -1
    second_page_index = -1
    txt = ""
    toc = ""
    found_abs = False
    found_kw = False
    found_eng = False
    similarity = False
    abs_page = None
    kw_index = None
    abs_index = None
    eng_index = None

    abs_text = ""
    for index, page in enumerate(pdf):
        lines = page.split("\n")
        for line_index, line in enumerate(lines):
            line = re.sub(r"\d", "", line)
            # if index > 5 and pdf_name == "/home/matic/Desktop/pdfji2/kas-7791.pdf":
            #    neki = "hdh
            while line.startswith(" ") or line.startswith("\t"):
                line = line[1:]
            while line.endswith(" "):
                line = line[:-1]
            if len(line) < 17 and "slik" not in line and "tabel" not in line and "prilog" not in line:
                # if line.count(".") < 3 and line.count("_") < 3 and line.count(" ") < 5 and len(line) < 20:

                first_word = re.sub(r"\d", "", line)
                first_word = first_word.replace(".", "")

                words = first_word.split(" ")

                if len([words]) < 3:
                    if not found_abs:
                        if sum([len(s.replace(" ", "")) for s in lines[line_index:]]) > 200:
                            for w in words:
                                if len(w):
                                    first_word = w.replace(" ", "").lower()
                                    for mark in toc_idx["kazalo"]:
                                        if not first_word.isdigit():
                                            similarity = similar(first_word, mark, conf=0.85)
                                            if similarity:
                                                found_abs = True
                                                abs_page = pdf[index].split("\n")[line_index + 1:]
                                                abs_index = line_index
                                                second_page_index = index + 1
                                                break
                                if found_abs:
                                    break
                    else:
                        break
            if found_abs:
                break
        if found_abs:
            break

    if found_abs:

        found_end = False
        new_abs_page = []
        while not len(abs_page[0]):
            del abs_page[0]
        counter = 0

        new_lines = []
        for line in abs_page:
            if line.endswith("-"):
                line_f = line[-5:-1]
                line_f = line_f.replace("-", "")
                line_f = line_f.replace(" ", "")
                line = line[0:-len(line_f)]
                line = line + line_f
            new_lines.append(line)
        abs_page = new_lines

        for line in abs_page:
            try:
                if not len(line.split()) or not len(line) or line == "\n":
                    counter += 1
                else:
                    new_abs_page.append(line)
                    if (line[-1].isdigit() or line.split()[-1].lower() in ["i", "ii", "iii", "iv", "v", "vi", "vii",
                                                                           "viii", "ix", "x", "xi", "xii", "xiii",
                                                                           "xiv", "xv", "xvi"]) and counter:
                        counter = 0

            except IndexError:
                pass
            if counter > 5:
                break

        counter = 0
        new_index = index
        while not found_end:
            index += 1
            abs_page = pdf[index].split("\n")
            new_lines = []
            for line in abs_page:
                if line.endswith("-"):
                    line_f = line[-5:-1]
                    line_f = line_f.replace("-", "")
                    line_f = line_f.replace(" ", "")
                    line = line[0:-len(line_f)]
                    line = line + line_f
                new_lines.append(line)
                new_index = index
            abs_page = new_lines
            for line in abs_page:
                if not len(line.split()) or not len(line) or line == "\n":
                    counter += 1
                else:
                    new_abs_page.append(line)
                    if counter and (
                            line[-1].isdigit() or line.split()[-1].lower() in ["i", "ii", "iii", "iv", "v", "vi", "vii",
                                                                               "viii", "ix", "x", "xi", "xii", "xiii",
                                                                               "xiv", "xv", "xvi"]):
                        counter = 0

                if counter > 5:
                    found_end = True
                    break

        abs_page = new_abs_page
        start_index = None
        end_index = 0
        conclusion_index = 0
        index_to_exclude = []

        abs_page = [i for i in abs_page if len(i)]

        conc = 0
        for j, line in enumerate(abs_page):
            old_line = line
            try:
                while old_line[-1] in ["i", "v", "x", ".", "_", "…", "\t", "-", " ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                    try:
                        old_line = old_line[:-1]
                    except IndexError:
                        old_line = ""
                        break
            except IndexError:
                old_line = ""
            if not len(old_line) > 3:
                old_line = "UNK"
            if len(line) > 3:
                while line[0].isdigit() or line[0] == " " or line[0] == "." or line[0] == "\t":

                    if len(line) > 3:
                        line = line[1:]
                    else:
                        break
                ind = 0
                new_line = ""
                while True:
                    try:
                        if not line[ind] in [".", "_", "…", "\t", "-"]:
                            new_line = line[0:ind + 1]
                        else:
                            break
                        if line[ind] == " " and line[ind + 1] == " " and line[ind + 2] == " ":
                            break
                        ind += 1
                    except IndexError:
                        break

                lines = new_line.split(" ")
                if len(lines) > 1:
                    a = lines[0].lower() + " " + lines[1].lower()
                else:
                    a = lines[0]

                b = lines[0].lower()

                old_line_2 = old_line
                try:
                    while old_line_2[0] in ["i", "v", "x", ".", "_", "…", "\t", "-", " ", "1", "2", "3", "4", "5", "6",
                                           "7", "8", "9", "0"]:
                        try:
                            old_line_2 = old_line_2[1:]
                        except IndexError:
                            old_line_2 = ""
                            break
                except:
                    old_line_2 = ""
                if not len(old_line_2):
                    old_line_2 = "UNK"

                if (similar("uvod", b, 0.85) or similar(old_line.lower(), "uvod", 0.7)) and start_index is None:
                    start_index = j
                elif ((similar("kazalo slik", a, 0.85)
                      or similar("kazalo tabel", a, 0.85)
                      or similar("viri", b, 0.85)
                      or similar("literatura", b, 0.85)
                      or similar("seznam slik", a, 0.85)
                      or similar("slika:", a, 0.92)
                      or similar("tabela:", a, 0.92)
                      or similar("seznam tabel", a, 0.85)) and start_index is not None
                      and a not in ["i", "ii", "iii", "iv", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii",
                                    "xiv", "xv", "xvi"]
                      and b not in ["i", "ii", "iii", "iv", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii",
                                    "xiv", "xv", "xvi"]) \
                      or similar(old_line.lower(), "literatura in viri", 0.8) \
                      or similar(old_line.lower(), "viri in literatura", 0.8):

                    end_index = j
                    if similar("viri", b, 0.85) and len([i for i in old_line_2.split() if len(i)]) > 1 and not similar(old_line.lower(), "viri in literatura", 0.8) and not similar(old_line.lower(), "literatura in viri", 0.8):
                        pass
                    else:
                        break

                elif (similar("sklep", b, 0.9) or similar("sklepne", b, 0.9)) and start_index is not None:
                    conclusion_index = j
                    conc += 1
                elif conc and not (similar("sklep", b, 0.9) or similar("sklepne", b, 0.9)) and start_index is not None:
                    break


        if end_index:
            abs_page = abs_page[start_index:end_index + 1]
        elif conclusion_index:
            abs_page = abs_page[start_index:conclusion_index + 2]
        else:
            abs_page = abs_page[start_index:]

        new_lines = []

        old_line = ""

        for i, line in enumerate(abs_page):

            if line[-1].isdigit():
                digit = True
            else:
                digit = False
            while line.startswith(" "):
                try:
                    if len(line):
                        line = line[1:]
                    else:
                        break
                except IndexError:
                    break
            if digit and len(old_line):
                line = old_line + " " + line
                old_line = ""
            if len(line):

                try:
                    while line[-1].isdigit() or line[-1] in [".", "_", "…", " ", "\t", "-"]:
                        try:
                            if len(line):
                                line = line[:-1]
                            else:
                                break
                        except IndexError:
                            break
                except IndexError:
                    pass

            if digit:
                new_lines.append(line)
            else:
                if len(line) and title.lower() not in line.lower():
                    if collections.Counter(line).most_common(1)[0] not in [" ", ".", "_", "…", " ", "\t", "-"] and \
                            line.split()[-1].lower() not in ["i", "ii", "iii", "iv", "vi", "vii", "viii", "ix", "x",
                                                             "xi", "xii", "xiii", "xiv", "xv", "xvi"]:
                        if len(line.split()) > 4:
                            old_line = line
            # abs_page[i] = line

        abs_page = new_lines
        for j, line in enumerate(abs_page):
            length = len(line)
            c = 0
            new_line = ""
            i = 0
            line = line.replace("\t", "")
            while i < length:
                if line[i] == " " and not c:
                    c += 1
                    new_line = new_line + line[i]
                else:
                    if line[i] != " ":
                        new_line = new_line + line[i]
                        c = 0

                i += 1
            new_line = new_line.replace("Ţ", "Ž")
            new_line = new_line.replace("ţ", "ž")
            new_line = new_line.replace("Ĉ", "Č")
            new_line = new_line.replace("Ĉ", "Č")
            new_line = new_line.replace("ĉ", "č")
            abs_page[j] = new_line
        abs_page = [i for i in abs_page if len(i) > 3]
        #abs_text = "\n".join(abs_page)
        #toc = "\n".join(abs_page)

        def norm2(line):
            length = len(line)
            c = 0
            new_line = ""
            i = 0
            line = line.replace("\t", "")
            while i < length:
                if line[i] == " " and not c:
                    c += 1
                    new_line = new_line + line[i]
                else:
                    if line[i] != " ":
                        new_line = new_line + line[i]
                        c = 0

                i += 1
            new_line = new_line.replace("Ţ", "Ž")
            new_line = new_line.replace("ţ", "ž")
            new_line = new_line.replace("Ĉ", "Č")
            new_line = new_line.replace("Ĉ", "Č")
            new_line = new_line.replace("ĉ", "č")
            return new_line

        def normalize(t):
            while t[0] in ["i", "v", "x", "\t", " ", "\f"]:
                t = t[1:]
            return t

        def get_intro():

            pdf = open(pdf_name, "r", encoding="utf-8").read()
            pdf = pdf.split("\n")
            pdf = [i for i in pdf if len(i) > 2]

            return pdf

        d = {}
        last_line = 0
        toc3_list = []
        for ind, toc in enumerate(abs_page):
            if ind < len(abs_page) - 1 and ind not in toc3_list:
                if name == "kas-7389.pdf":
                    xj = "ihud"
                name_toc = toc
                start = None
                end = None
                sim, sim2 = 0, 0
                if ind < len(abs_page) - 1:
                    pdf = get_intro()
                    try:
                        toc = normalize(toc)
                    except IndexError:
                        toc = toc
                    try:
                        toc2 = normalize(abs_page[ind+1])
                    except IndexError:
                        toc2 = abs_page[ind+1]
                    try:
                        toc3 = normalize(abs_page[ind+2])
                    except IndexError:
                        toc3 = ""

                    for i, line in enumerate(pdf[last_line:]):
                        try:
                            line = norm2(line)
                            line = normalize(line)
                        except IndexError:
                            line = norm2(line)
                        #if start is None:
                        if len(line) > len(toc) and len(line) > 3:
                            sim = similar(toc.lower(), line[:len(toc)].lower(), 0.94)
                        elif len(line) > 3:
                            sim = similar(toc[:len(line)].lower(), line.lower(), 0.94)
                        else:
                            sim = False
                        #if end is None:
                        if len(line) > len(toc2) and len(line) > 3:
                            sim2 = similar(toc2.lower(), line[:len(toc2)].lower(), 0.94)
                        elif len(line) > 3:
                            sim2 = similar(toc2[:len(line)].lower(), line.lower(), 0.94)
                        else:
                            sim2 = False
                        if len(line) > len(toc3) and len(line) > 3:
                            sim3 = similar(toc3.lower(), line[:len(toc2)].lower(), 0.94)
                        elif len(line) > 3:
                            sim3 = similar(toc3[:len(line)].lower(), line.lower(), 0.94)
                        else:
                            sim3 = False
                        if sim:# and start is None:
                            start = i + last_line
                        if sim2 or sim3: # and start is not None and end is None:
                            if sim2:
                                end = i + last_line
                            else:
                                end = i + last_line - 1
                        if start is not None and end is not None and len(" ".join([i for i in pdf[start + 1:end] if len(i.replace(" ", "").replace("\t", "")) > 5 and title not in i])) > 10:
                            last_line = end - 1
                            break
                        elif start is not None and end is not None:
                            start = None
                            end = None
                        elif start is None and end is not None:
                            start = None
                            end = None

                written = False
                if start is not None and end is not None:
                    txt = " ".join([i for i in pdf[start + 1:end] if (len(i.replace(" ", "").replace("\t", "")) > 50 or (5 < len(i.replace(" ", "").replace("\t", "")) and i[-1] in [".", ":", ";", "!", "?"])) and title not in i])
                    if len(txt) > 100:
                        txt = txt.replace("Ţ", "Ž")
                        txt = txt.replace("ţ", "ž")
                        txt = txt.replace("Ĉ", "Č")
                        txt = txt.replace("Ĉ", "Č")
                        txt = txt.replace("ĉ", "č")
                        txt = txt.replace("\t", " ")
                        txt = txt.replace("\f", "")
                        if not sim3:
                            d[ind+1] = [name_toc, txt]
                            #d[name_toc] = txt
                        else:
                            toc3_list.append(ind+1)
                            d[ind+1] = ["{0} | {1}".format(name_toc, abs_page[ind + 1]), txt]
                            #d["{0} | {1}".format(name_toc, abs_page[ind + 1])] = txt
                        written = True
                if not written:
                    d[ind+1] = [name_toc, ""]
                    #d[name_toc] = ""
        with open(f"/media/matic/My Passport/kas_segmented_2/{name.replace('.txt', '.json')}", 'w', encoding='utf-8') as f:
            #with open(f"./povzetki/{name.replace('.pdf', '.txt')}", "r") as abstract:
            #    a = abstract.read()
            #if len(a) > 30:
            #d[0] = ["Povzetek", a]
            json.dump(d, f, ensure_ascii=False)
            f.write("\n")
            f.close()
        #for i in d:
        #    print(d[i])

    #if similarity:
    #    with open(f"./kazala/{name.replace('.pdf', '')}.txt", "w", encoding='utf-8') as f:
    #        if similarity:
    #            f.writelines(toc)
    #        else:
    #            pass
    #            #f.writelines("Ne najdem kazala")
    #    f.close()
    #    #time.sleep(0.01)
    s_c.update()
    #return None


#main_loop(0, "kas-2901.txt", sum_count, "kas-2901.txt")

test = False
if not test:



    from queue import Queue
    with sum_count as s_c:

        #threads = []
        #tm = time.time()
        #jobs = Queue()
        for j, name in enumerate(natsorted(os.listdir(base_name))):

            #a = threading.Thread(target=main_loop, args=[j, name, base_name, s_c, ])
            #threads.append(a)
            #p = mp.Pool()
            #p.starmap(main_loop, [(j, name, base_name, s_c)])
            #p.close()
            #p.join()
            #s_c.update()
            #s_c.update()
            try:
                main_loop(j, name, base_name, s_c)
            except:
                pass
            #break
        #for t in threads:
        #    t.start()
        #for t in threads:
        #    t.join()
        #print(time.time() - tm)


        #import concurrent.futures
        #import multiprocessing

        #max_workers = multiprocessing.cpu_count()
        #
        #tm = time.time()
        #with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        #    futures = []
        #    for j, name in enumerate(natsorted(os.listdir(base_name))):
        #        futures.append(executor.submit(main_loop, j=j, name=name, base_name=base_name, s_c=None))
        #    for future in concurrent.futures.as_completed(futures):
        #        s_c.update()
        #print(time.time() - tm)
        """
        tm = time.time()
        for j, name in enumerate(natsorted(os.listdir(base_name))):
            main_loop(j, name, base_name, s_c)
        print(time.time() - tm)
        """
