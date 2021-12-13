import re
import collections
from natsort import natsorted
import os
import tqdm
import multiprocessing
from cdifflib import CSequenceMatcher

SequenceMatcher = CSequenceMatcher


PATTERNS = {
    "slika": '^( +)?(slika)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "tabela": '^( +)?(tabela)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "preglednica": '^( +)?(preglednica)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "graf": '^( +)?(graf)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "grafikon": '^( +)?(grafikon)( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "prikaz": '^( +)?( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "vir": '^( +)?(vir)(i)?( podatkov)?( +)?:',
    "page_num": "^(\f)?(-)?( +)?[0-9]{1,3}( +)?(-)?$",
    "picture": '^( +)?( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "table": '^( +)?( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
    "graph": '^( +)?( +)(\d){1,3}( +)?([:]|( +)?(.+)?( +)?(\d){1,3}( +)?[.,:]( +)?(:)?)',
}

PUNCTUATIONS = [".", ",", "!", "?", ":", ";", "…"]


def remove_noise(txt, figs=False):
    txt = re.sub(" +", " ", txt)
    txt = txt.replace("¾", "-")
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
    txt = txt.replace('·', '-')
    txt = txt.replace('◦', '-')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('°', '-')
    txt = txt.replace('⁰', '-')
    txt = txt.replace('º', '-')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('­', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('●', '-')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('‫', '')
    txt = txt.replace('‬', '')
    txt = txt.replace('', '')
    txt = txt.replace(' ', '')
    txt = txt.replace('', '')
    txt = txt.replace('', '')
    txt = txt.replace('⁯', '')
    txt = txt.replace('⁭', '')
    txt = txt.replace('', '-')
    txt = txt.split("\n")
    indexes_to_remove = []

    if figs:
        for idx, line in enumerate(txt):
            check_second = False
            second_idx = 0
            if len(line):
                for key in PATTERNS.keys():
                    pattern = PATTERNS[key]
                    if re.match(pattern, line.replace("\f", ""), re.IGNORECASE):
                        if "\f" not in line:
                            indexes_to_remove.append(idx)
                        else:
                            txt[idx] = "\f"
                        check_second = True
                    try:
                        while check_second:
                            second_idx += 1
                            if txt[idx + second_idx].islower() \
                                    and len(txt[idx + 1]) < len(line) \
                                    and txt[idx + 1][-1] not in PUNCTUATIONS:
                                if "\f" not in txt[idx + second_idx]:
                                    indexes_to_remove.append(idx + second_idx)
                                else:
                                    txt[idx+second_idx] = "\f"
                            else:
                                check_second = False
                    except IndexError:
                        pass

    new_txt = "\n".join([line for idx, line in enumerate(
        txt) if idx not in indexes_to_remove])
    return new_txt


def similar(a: str, b: str, conf: float = 0.6):
    ratio = SequenceMatcher(None, a, b).ratio()
    similarity = True if ratio >= conf else False
    return similarity


def remove_pn(txt):
    lines = txt.split("\n")
    ind_remove = []
    for ind, line in enumerate(lines):
        if re.match("^(\f)?( +)?(-)?( +)?[0-9]{1,3}( +)?(-)?( +)?$", line, re.IGNORECASE):
            if not "\f" in line:
                ind_remove.append(ind)
            else:
                lines[ind] = "\f"
    new_txt = "\n".join(
        [i for ind, i in enumerate(lines) if ind not in ind_remove])
    return new_txt


def is_roman(word):
    pattern = re.compile(r"""  
                                ^M{0,3}
                                (CM|CD|D?C{0,3})?
                                (XC|XL|L?X{0,3})?
                                (IX|IV|V?I{0,3})?$
            """, re.VERBOSE)

    return True if re.match(pattern, word) and len(word) > 0 else False


def remove_roman_pn(txt):
    lines = txt.split("\n")
    for ind, line in enumerate(lines):
        line = line.replace("-", "").replace(" ", "").upper().split()
        if len(line) == 1:
            if is_roman(line[0]):
                lines[ind] = "\n"
    new_txt = "\n".join([i for ind, i in enumerate(lines)])
    return new_txt


def main(name):
    try:
        start = None
        end = None
        toc = os.path.join(toc_path, name)
        pdf_name = os.path.join(base_name, name)
        title = "UNKNOWNUNKNOWNUNKNOWN"
        toc_txt = open(toc).read()
        toc_txt2 = toc_txt
        toc_txt = "\n".join(toc_txt.split("\n")[1:])

        toc_txt = remove_pn(toc_txt)
        abs_page = toc_txt.split("\n")
        abs_page = [i for i in abs_page if len(i) > 2]

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

        if len(new_lines) > len(abs_page)//100*60:
            pass
        else:
            new_lines = []
            for line in abs_page:
                try:
                    while not line[-1].isalpha() and not is_roman(line.split()[-1].upper()):
                        line = line[:-1]
                    new_lines.append(line)
                except:
                    pass
        abs_page = [remove_noise(i) for i in new_lines]
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

        def get_intro(last_line):
            pdf = open(pdf_name, "r", encoding="utf-8").read()
            pdf2 = pdf.split("\n")
            pdf = pdf2[last_line:]
            cut = pdf2[:last_line]
            pdf = "\n".join(pdf)
            pdf = remove_noise(pdf, True)
            pdf = remove_pn(pdf)
            pdf = remove_roman_pn(pdf)
            pdf = pdf.split("\n")
            return pdf, cut

        def norma(txt):
            txt = txt.replace("\f", "")
            txt = txt.replace("\n", "")
            txt = re.sub(" +", " ", txt)
            txt = re.sub("([. _]?)+[\d]+$", "", txt)
            txt = re.sub("^_+", "", txt)
            return txt.lower()

        last_line = int(toc_txt2.split("\n")[0])
        page_begin = 0
        pdf, cut = get_intro(last_line)
        abs_page2 = abs_page
        abs_page = [abs_page[0], abs_page[-1]]

        for ind, toc in enumerate(abs_page):
            if ind == 1:
                break

            toc = norma(toc)
            toc2 = norma(abs_page[ind+1])
            start = None
            sim = False
            sim2 = False
            end = None

            for i, line in enumerate(pdf):
                line2 = norma(line)

                if start is None and len(line2) < len(toc) + 7 and not re.match(".*[_ .…]+[\d]{1,2}$", line):
                    if similar(line2, toc, 0.6):
                        sim = True

                if start is not None and len(line2) < len(toc2) + 7:
                    if similar(line2, toc2, 0.6):
                        sim2 = True
                    elif "".join([x for x in line2 if x.isalpha()]) in ["povzetek", "povzetekinsummary", "povzeteksummary"] and len(line2) > 1 and line2[-1] not in PUNCTUATIONS:
                        sim2 = True

                if sim:
                    start = i
                    sim = False

                if sim2:
                    end = i

                new = True
                s = True
                previous = False
                txt = ""

                if start is not None and end is not None:
                    for line in pdf[start:end]:
                        if line != "":
                            n = True if re.search("^([ ]+)?-", line) else False
                            h = True if re.search(
                                "^[ +]?|([\d]{1,3}([. ]+)?)+", line) else False

                            if not n:
                                t = False
                                if h:
                                    for toc in abs_page2:
                                        if similar(norma(line), norma(toc), 0.94):
                                            t = True
                                            break
                                if not t:
                                    if not previous:
                                        txt = txt+" "+line if not new else txt+line
                                    else:
                                        txt = txt+" "+line
                                        previous = False
                                    new = False
                                    s = False
                                else:
                                    txt = txt + "\n" + line + "\n"
                                    new = False
                                    s = False
                                    previous = True
                            else:
                                txt = txt + "\n" + line
                                new = False
                                s = False
                                previous = True

                        else:
                            if not s:
                                txt = txt+"\n"
                                new = True
                                s = True
                                previous = False

                    page_begin = "".join(pdf[:start + 1]).count("\f") + 1
                    txt = txt.split("\n")
                    txt = [re.sub("[ ]+?$", "", i) for i in txt if len(i)]
                    txt = [re.sub("^[ ]*", "", i) for i in txt if len(i)]

                    new_txt = []
                    for j, line in enumerate(txt):
                        line2 = norma(line)
                        if len(line2) < 100:
                            for ind, toc in enumerate(abs_page2):
                                if similar(line2, norma(toc), 0.9):
                                    heading1 = line.replace(
                                        "\n", "").replace("\f", "")
                                    heading = heading1.replace(
                                        ".", " ").split(" ")
                                    num_h = 0
                                    for x in heading:
                                        if x.isnumeric():
                                            if int(x) < 1000:
                                                num_h += 1
                                        else:
                                            break
                                    if not num_h:
                                        num_h = 1
                                    if not "\f" in line or not j:
                                        line = f"<h.{num_h}>{heading1}</h.{num_h}>" + "\n"
                                    else:
                                        line = "\f"+"\n" + \
                                            f"<h.{num_h}>{heading1}</h.{num_h}>" + "\n"
                                    break

                        new_txt.append(line)

                    txt = "\n".join(new_txt)

                    page_begin = "".join(cut).count(
                        "\f") + "".join(pdf[:start+1]).count("\f") + 1
                    h = txt.split("\f")
                    h = [i for i in h]
                    txt = ""
                    for i in h:
                        txt = txt + "\n" + f"<pn>{page_begin}</pn>" + "\n" + i
                        page_begin += 1
                    txt = txt.split("\n")
                    h = [i for i in txt if len(i) > 1]
                    try:
                        if h[-1] == "\n":
                            h = h[0:-1]
                    except IndexError:
                        pass
                    h = [
                        f"<p>{i}</p>" if "<pn>" not in i and "</pn>" not in i else i for i in h]
                    txt = "\n".join(h)

                    if start is not None and not page_begin:
                        page_begin = "".join(pdf[:start+1]).count("\f")+1

                    if start is not None and end is not None:
                        if len(txt.split("\n")) > 20:
                            with open(f"./metatxt/{name}", 'w', encoding='utf-8') as f:
                                f.write(txt)
                                f.close()
                            break
            break
    except:
        pass


base_name = "./figures_txt"
toc_path = "./toc"
all_pdfs = natsorted(os.listdir(toc_path), reverse=True)

cpu_count = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
with multiprocessing.Pool(cpu_count) as p:
    r = list(tqdm.tqdm(p.imap_unordered(main, all_pdfs), total=len(all_pdfs)))
