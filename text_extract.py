import shutil
import subprocess
import tqdm
import os
import pandas as pd
import re
from difflib import SequenceMatcher

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


def similar(a: str, b: str, conf: float = 0.6):
    ratio = SequenceMatcher(None, a, b).ratio()
    similarity = True if ratio >= conf else False
    return similarity, ratio


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


#figures = pd.read_csv("./kas_figures.csv", sep="|", converters={"figures": eval})
base_name = "/media/matic/My Passport/kas_new_text"

#names = figures["id"].tolist()
sum_count = tqdm.tqdm(total=87706)

"""
names = [name.replace(".pdf", ".txt") for name in names]
base_name = "/media/matic/My Passport/FRI/KAS/KAS-txt/kas.txt"
with sum_count as s_c:
    for dir, folder, files in os.walk(base_name):
        for j, name in enumerate(files):
            if name.endswith(".txt") and "kas-" in name and name in names:  # and name in files2:
                pdf_name = os.path.join(dir, name)
                shutil.copyfile(pdf_name, os.path.join("./test_txt_old_kas", name))

"""


with sum_count as s_c:
    for dir, folder, files in os.walk(base_name):
        for j, name in enumerate(files):
            if name.endswith(".txt") and "kas-" in name:  # and name in files2:
                try:
                    text = open(f"/media/matic/My Passport/kas_new_text/{name}", "r", encoding="utf-8")

                    text = "".join([i for i in text])

                    text = remove_noise(text, False)
                    text = text.split("\n")
                    start = 0
                    end = -1
                    for ind, t in enumerate(text):
                        b = t.lower()
                        spaces = b.count(" ")
                        if spaces < 11:
                            b = b.replace(" ", "")
                        if not b.endswith("."):
                            if not start:
                                if similar("uvod", b, 0.7)[0] or similar("uvodzopredelitvijoproblema", b, 0.7)[0] or similar("1opredelitevproblema", b, 0.7)[0] or similar("1uvod", b, 0.7)[0] or similar("1\tuvod", b, 0.7)[0]:
                                    start = ind

                            if start:
                                if (similar("literatura", b, 0.9)[0] and "literatura." not in b and "literaturah" not in b and "literaturo" not in b and not b.endswith(":")) or \
                                        (similar("viri", b, 0.7)[0] and ("vir:" not in b and "vir" != b and "vir." not in b and "virih" not in b and "viri." not in b and not b.endswith(":"))) or \
                                        similar("viriinliteratura", b, 0.7)[0] or \
                                        similar("literaturainviri", b, 0.7)[0] or \
                                        similar("seznamliteratureinvirov", b, 0.7)[0] or \
                                        similar("seznamliterature", b, 0.7)[0] or \
                                        similar("seznamvirov", b, 0.7)[0] or \
                                        similar("povzetek", b, 0.9)[0]:
                                    end = ind
                            if start and end > 0:
                                break

                    if start and end < 0:
                        for ind, t in enumerate(text):
                            b = t.lower()
                            spaces = b.count(" ")
                            if spaces < 11:
                                b = b.replace(" ", "")
                            if similar("seznamvirov", b, 0.7)[0] or similar("uporabljeniviri", b, 0.7)[0]:
                                end = ind

                    if start and end > 0:
                        text = text[start:end]
                        new_text = []
                        s = -1
                        e = -1
                        for j, i in enumerate(text):
                            if len(i) and s == -1:
                                s = j
                            if s != -1 and not len(i):
                                e = j
                            if e != -1:
                                t = ""
                                add = " "
                                for nn, h in enumerate(text[s:e]):
                                    if nn == len(text[s:e])-1:
                                        add = ""
                                    if not h.startswith("-") or not len(t):
                                        t = t + h + add
                                    else:
                                        t = t + "\n" + h + add
                                #t = " ".join([h for h in text[s:e]])
                                e = -1
                                s = -1
                                new_text.append(t)

                        text = "\n".join([i for i in new_text])
                        text = remove_noise(text, True)



                        ends = [".", "!", "?", ":", ";"]
                        """
                        new_text = ""
                        for line in text.split("\n"):
                            temp = line.replace(" ", "")
                            if len(temp) > 15 and not line.endswith(":") and not line.startswith("-"):
                                new_text = new_text+line+"\n"
                        space = " "
                        for k in range(20):
                            space = space + " "
                            text = text.replace(space, " ")
                        """
                        new_lines = text.split("\n")
                        ind_to_r = []
                        for num, line in enumerate(new_lines):
                            if len(line) < 3:
                                if line[-1] not in ends:
                                    ind_to_r.append(num)
                        lines = []
                        for num, line in enumerate(new_lines):
                            if num not in ind_to_r:
                                lines.append(line)
                        text = "\n".join(lines)


                        with open(f"/media/matic/My Passport/kas_new_text_cut/{name}", "w", encoding="utf8", newline='\n') as f:
                            f.write(text)
                            f.flush()
                            f.close()
                    else:
                        with open("./logging_last.txt", "a") as tmp_t:
                            tmp_t.write(f"{name} {start} {end}")
                            tmp_t.write("\n")
                except:
                    with open("./logging_last.txt", "a") as tmp_t:
                        tmp_t.write(f"{name} ERROR")
                        tmp_t.write("\n")
                s_c.update(1)
                s_c.refresh()
