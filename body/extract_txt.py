from natsort import natsorted
import subprocess
import tqdm
import os
import pandas as pd
import re
import multiprocessing
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher

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
    txt = txt.replace("ĉ", "č")
    txt = txt.replace("Ċ", "Č")
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

    new_txt = "\n".join([i for idx, i in enumerate(txt)
                        if idx not in indexes_to_remove])
    return new_txt


figures = pd.read_csv("./figures/figures.csv", sep="|",
                      converters={"figures": eval})
base_name = "./PDF"

names = figures["id"].tolist()


f = []
for dir, folder, files in reversed(list(os.walk(base_name, ))):
    for j, name in enumerate(files):
        if name.endswith(".pdf") and name.replace(".pdf", "") in names:
            f.append(f"{dir}/{name}")

f = natsorted(f)


def main(variables):
    try:
        name = variables[0]
        direct = variables[1]
        figs = variables[2]
        landscape = variables[3]
        text = []
        for num, page in enumerate(figs):
            pg = []
            for area in page:
                y1 = area[0]
                y2 = area[1]
                if not landscape:
                    txt = subprocess.check_output(
                        f'pdftotext -y {y1} -H {y2} -f {num + 1} -l {num + 1} -W 1000 -nopgbrk -layout -enc "UTF-8" -r 72 -q {direct}/{name} -',
                        # -y {offset} -H {bottom} -r 72
                        shell=True,
                        encoding="UTF-8")
                else:
                    txt = subprocess.check_output(
                        f'pdftotext -y {y1} -H {y2} -f {num + 1} -l {num + 1} -W 1000 -nopgbrk -enc "UTF-8" -r 72 -q {direct}/{name} -',
                        # -y {offset} -H {bottom} -r 72
                        shell=True,
                        encoding="UTF-8")
                txt = txt.replace("\f", "")
                txt = txt.replace("", "")
                pg.append(txt)
            pg = ("\n" + "\n").join(pg)
            text.append(pg)
            text.append("\f")

        text = "".join([i for i in text])

        with open(f"./figures_txt/{name.replace('.pdf', '.txt')}", "w", encoding="utf8", newline='\n') as f:
            f.write(text)
            f.flush()
            f.close()
    except:
        pass


list1 = []
for j, dir in enumerate(f):
    ind = 0
    for h in reversed(dir):
        if h != "/":
            ind += 1
        else:
            break
    name = dir[-ind:]
    direct = dir[0:-ind]
    status = figures.loc[figures["id"] == name.replace(
        ".pdf", "")]["status"].tolist()[0]
    if status:
        figs = figures.loc[figures["id"] == name.replace(
            ".pdf", "")]["figures"].tolist()[0]
        landscape = figures.loc[figures["id"] == name.replace(
            ".pdf", "")]["error"].tolist()[0]
        landscape = 1 if isinstance(landscape, str) else 0
        list1.append([name, direct, figs, landscape])


cpu_count = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
with multiprocessing.Pool(cpu_count) as p:
    r = list(tqdm.tqdm(p.imap_unordered(main, list1), total=len(list1)))
