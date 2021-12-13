import os
import shutil

os.makedirs("./figures", exist_ok=True)
os.makedirs("./figures_txt", exist_ok=True)
os.makedirs("./metatxt", exist_ok=True)
os.makedirs("./toc", exist_ok=True)

try:
    print("1/5 - Extracting figures")
    os.system("python3 extract_figures.py")
    print("2/5 - Extracting whole tekst")
    os.system("python3 extract_txt.py")
    print("3/5 - Extracting table of contents")
    os.system("python3 extract_toc.py")
    print("4/5 - Extracting metatxt")
    os.system("python3 extract_body.py")
    print("5/5 - Extracting txt and json")
    os.system("python3 metatxt_to_txt_json.py")

except:
    pass

print("DONE - look in the folder containing .pdf files - there should be two new folders containing body text.")
shutil.rmtree("./figures")
shutil.rmtree("./figures_txt")
shutil.rmtree("./metatxt")
shutil.rmtree("./toc")
if os.path.isfile("./figures.jsonl"):
    os.remove("./figures.jsonl")
