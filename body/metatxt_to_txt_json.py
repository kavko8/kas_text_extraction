from bs4 import BeautifulSoup
import os
import json
import tqdm

headings = ["h" + f"{x}" for x in range(1000)]

directory = "./metatxt"
onlyfiles = [os.path.join(path, name) for path, subdirs, files in os.walk(
    directory) for name in files if name.endswith(".txt")]

t_q = tqdm.tqdm(total=len(onlyfiles))

with t_q as tq:
    for file in onlyfiles:
        with open(file, "r") as txt_file:
            txt = txt_file.read()

        file = file.replace(".txt", "")
        folder_name = file[-3:]
        filename = file.split("/")[-1]
        soup = BeautifulSoup(txt, features="html.parser")
        new_txt = ""
        heading_num = 0
        json_obj = {}

        for div_tag in soup.select('p'):
            if div_tag.find(lambda t: t.name not in headings):
                new_txt = new_txt + div_tag.text + "\n"
                current_heading = div_tag.text
                heading_num += 1
                json_obj[heading_num] = [current_heading, ""]
            else:
                json_obj[heading_num][1] = json_obj[heading_num][1] + \
                    div_tag.text + "\n"
                new_txt = new_txt + div_tag.text + "\n"

        os.makedirs("./PDF/txt", exist_ok=True)
        os.makedirs("./PDF/json", exist_ok=True)

        with open(f"./PDF/json/{filename}.json", "w", encoding="utf-8") as json_file:
            json.dump(json_obj, json_file, indent=4, ensure_ascii=False)

        with open(f"./PDF/txt/{filename}.txt", "w", encoding="utf-8") as txt_file:
            txt_file.write(new_txt)

        tq.update(1)
        tq.refresh()
