import multiprocessing
import tqdm
import os
import re
from natsort import natsorted
import collections
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher


END_TRIGGERS = [
    "viri", "literatura", "viriinliteratura", "literaturainviri", "seznamliterature", "seznamvirov", "sklep",
    "sklepnemisli", "zakljucek", "zakljucki", "seznamuporabljeneliteratureinvirov", "seznamuporabljeneliterature",
    "seznamuporabljenihvirov", "seznamslik", "seznamtabel", "sklepneugotovitve", "zakljucekinverifikacijahipotez",
    "povzetek", "povzetek-summary", "povzetek/abstract", "povzetekinsummary", "izvleček", "uporabljenaliteraturainviri",
    "uporabljenaliteratura", "uporabljeniviri", "sklepnabeseda""seznamvirovinliterature", "seznampreglednicslikgrafovinprilog",
    "zakljucekconclusion", "zakljuckiconclusions", "bibliografija", "ugotovitveinsklepnemisli", "delugotovitveinsklepnemisli",
    "razpravainzakljucek", "primerjavarezultatovinzakljucek", "priloge", "slovstvoinviri", "studijskaliteratura", "povzetekvslovenskemintujemjeziku",
]

PATTERNS = {
    "slika": '^( +)?(slika)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "tabela": '^( +)?(tabela)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "preglednica": '^( +)?(preglednica)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "graf": '^( +)?(graf)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "grafikon": '^( +)?(grafikon)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "prikaz": '^( +)?( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "vir": '^( +)?(vir)(i)?( +)?:',
    "page_num": "^(\f)?(-)?( +)?[0-9]{1,3}( +)?(-)?$",
}

PUNCTUATIONS = [".", ",", "!", "?", ":", ";", "…"]


LITERATURE = [
    "studijskaliteratura",
    "primerjavarezultatovinzakljucek",
    "zakljucki",
    "sklep",
    "sklepnemisli",
    "zakljucek",
    "zakljucekinverifikacijahipotez",
    "zakljucekconclusion", "zakljuckiconclusions",
    "sklepnabeseda", "ugotovitveinsklepnemisli",
    "delugotovitveinsklepnemisli",
    "razpravainzakljucek",
    "primerjavarezultatovinzakljucek"
]

BEGINS = [
    "teoretičniuvod",
    "uvodinopredelitevproblema",
    "uvod",
    "uvodinopisproblema",
    "uvodzopredelitvijoproblema",
    "uvodinnamen", "poglavjeuvod",
    "deluvodinpredstavitevteme",
    "deluvod"
]

FIGURES = [
    "kazalopreglednic",
    "kazaloslik",
    "kazalotabel",
    "kazalografov",
    "kazalografikonov",
    "kazaloprikazov",
    "seznampreglednic",
    "seznamslik",
    "seznamtabel",
    "seznamgrafov",
    "seznamgrafikonov",
    "seznamprikazov",
    "kazaloslikintabel",
    "seznamslikintabel",
    "seznamvirov"
]


def is_roman(word):
    pattern = re.compile(r"""   
                                ^M{0,3}
                                (CM|CD|D?C{0,3})?
                                (XC|XL|L?X{0,3})?
                                (IX|IV|V?I{0,3})?$
            """, re.VERBOSE)

    return True if re.match(pattern, word) and len(word) > 0 else False


def normalize_toc(lines):
    old_line = ""
    new_lines = []
    for i, line in enumerate(lines):
        if len(line):
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

            if digit and not is_roman(line.upper().replace(" ", "").replace("\f", "").replace("\n", "")):
                new_lines.append(line)
            else:
                if len(line) > 1:
                    if collections.Counter(line).most_common(1)[0] not in [" ", ".", "_", "…", " ", "\t", "-"] and \
                            line.split()[-1].lower() not in ["i", "ii", "iii", "iv", "vi", "vii", "viii", "ix", "x",
                                                             "xi", "xii", "xiii", "xiv", "xv", "xvi"]:
                        if len(line.split()) > 4:
                            old_line = line
    new_lines = [re.sub(" +", " ", l) for l in new_lines]
    return new_lines


def similar(a: str, b: str, conf: float = 0.6):
    ratio = SequenceMatcher(None, a, b).ratio()
    similarity = True if ratio >= conf else False
    return similarity, ratio


def remove_pn(txt):
    lines = txt.split("\n")
    for ind, line in enumerate(lines):
        if re.match("^(\f)?(-)?( +)?[0-9]{1,3}( +)?(-)?$", line, re.IGNORECASE):
            lines[ind] = "\n"
    new_txt = "\n".join([i for i in lines])
    return new_txt


def remove_roman_pn(txt):
    lines = txt.split("\n")
    for ind, line in enumerate(lines):
        line = line.replace("-", "").replace(" ", "").upper().split()
        if len(line) == 1:
            if is_roman(line[0]):
                lines[ind] = "\n"
    new_txt = "\n".join([i for ind, i in enumerate(lines)])
    return new_txt


def main(arguments):
    try:
        name = arguments[0]
        path = arguments[1]
        with open(path, "r") as text:
            all_pages_text2 = text.read()
        all_pages_text = remove_pn(all_pages_text2)
        all_pages_text = remove_roman_pn(all_pages_text)
        all_pages_text = all_pages_text.replace("\f", "")
        lines = all_pages_text.split("\n")

        start = None
        end = None
        intro = False
        not_roman_counter = 0
        sklepne = False
        good_end = False
        for line_index, line in enumerate(lines):
            line = re.sub(" Napaka! .*", f"{line_index}", line)
            line = re.sub(" NAPAKA! .*", f"{line_index}", line)
            old_line = line
            start_word = ''.join(x for x in line.replace(" str. ", "").replace(
                "Str. ", "").replace(" STR. ", "") if x.isalpha()).lower()

            if not intro and start_word in BEGINS:
                start = line_index
                intro = True

            if start is None and start_word in ["kazalo", "kazalovsebine", "vsebina"]:
                start = line_index+1
                while not len(lines[start].replace("\n", "")):
                    start = start + 1
                while similar(''.join(x for x in lines[start].replace(" str. ", "").replace("Str. ", "").replace(" STR. ", "") if x.isalpha()).lower(), "kazalo", 0.9)[0]:
                    start += 1

            if start is None and re.match("(.*?)[\W]{10,100}(\d+)(?=\n|$)", line):
                line = [x for x in re.sub(
                    "[._… ]", " ", line).split(" ") if len(x) > 3]
                if not len(line):
                    start = line_index

            if start is not None and not_roman_counter < 3:
                if len(old_line) > 1:

                    if is_roman(re.split("[._…]", old_line)[-1].upper()):
                        start = None
                    else:
                        not_roman_counter += 1

            if start is not None and line_index > start + 10:
                words = ''.join(x for x in line if x.isalpha()).lower().replace(
                    "č", "c").replace("š", "s").replace("ž", "z")
                for i in END_TRIGGERS:
                    if similar(words, i, 0.9)[0]:
                        if i in LITERATURE:
                            end = line_index+1
                            for additional in lines[end:]:
                                end = end + 1
                                words_next = ''.join(x for x in additional if x.isalpha()).lower().replace("č", "c").replace(
                                    "š", "s").replace("ž", "z")
                                words_next_bool = False

                                for x in END_TRIGGERS:
                                    if similar(words_next, x, 0.9)[0] and x not in ["sklep"]:
                                        words_next_bool = True
                                        break

                                if words_next_bool:
                                    break

                                if len(additional) > 5:
                                    add = [i for i in re.split(
                                        "[ ,.]", additional) if len(i)]
                                    if len(add):
                                        if len(add[0]) > 2:
                                            break
                                        else:
                                            if len(add) > 1:
                                                if not all(c.isnumeric() for c in add[:2]):
                                                    break
                            good_end = True
                            sklepne = False

                        elif i == "sklepneugotovitve":
                            end = line_index+1
                            sklepne = True

                        else:
                            sklepne = False
                            end = line_index
                            temp_words = "".join(x for x in lines[end] if x.isalpha()).lower().replace("č", "c").replace(
                                "š", "s").replace("ž", "z")

                            if "viri" not in temp_words and "literatura" not in temp_words:
                                for additional in lines[end:]:
                                    end = end + 1
                                    if len(additional) > 5:
                                        break

                            else:
                                end = end + 1

                        break

                if end is None:
                    for i in FIGURES:
                        if similar(words, i, 0.8)[0]:
                            sklepne = False
                            end = line_index

            if end is not None and not sklepne:
                ending = False
                while not ending:
                    x = re.sub("[. _-]", "", lines[end])
                    if len(x):
                        ending = True
                        break
                    else:
                        end += 1
                break

        new_toc = lines[start:end]
        if start is not None and end is not None:
            alpha_counter = 0
            for l in lines[start:end]:
                t = l.split()
                for ll in t:
                    if ll.isalpha():
                        alpha_counter += 1

            if ((10 < len(new_toc) < 300) or (intro and good_end)) and alpha_counter < 1000:
                end = 0
                new_toc = [i for i in new_toc if len(i) > 1]
                for ind, i in enumerate(all_pages_text2.split("\n")):
                    if similar(i.replace("\f", "").replace("\n", ""), new_toc[-1].replace("\f", "").replace("\n", ""), 0.8)[0]:
                        end = ind + 1
                        break

                numbers = len([l for l in new_toc if len(l)
                               > 1 and l[-1].isnumeric()])
                percent = (
                    len([l for l in new_toc if len(l) > 1]) // 100) * numbers
                if percent > 60:
                    new_toc = normalize_toc(new_toc)
                else:
                    new_toc = [re.sub(" +", " ", l)
                               for l in new_toc if len(l) > 1]
                if len(new_toc) > 10:
                    with open(f"./toc/{name}", "w", encoding="utf8", newline='\n') as f:
                        f.write(f"{end}"+"\n"+"\n".join([i for i in new_toc]))
                        f.flush()
                        f.close()
    except:
        pass


base_name = "./figures_txt"
all_pdfs = []
weird_chars = []


for path, folder, files in os.walk(base_name):
    for name in files:
        if name.endswith(".txt"):
            all_pdfs.append([name, os.path.join(path, name)])

all_pdfs = natsorted(all_pdfs)


cpu_count = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
with multiprocessing.Pool(cpu_count) as p:
    r = list(tqdm.tqdm(p.imap_unordered(main, all_pdfs), total=len(all_pdfs)))
