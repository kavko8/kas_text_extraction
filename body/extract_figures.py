import multiprocessing
import json
import cv2
from pdf2image import convert_from_path
import numpy as np
import tqdm
import os
import subprocess
import pandas as pd
from natsort import natsorted


class NotEnoughPagesError(Exception):
    pass


class Figures:
    def __init__(self, path=None, name=None, thread_count=1):
        self.pdf_name = path
        self.name = name
        self.thread_count = thread_count

    def main(vals):
        try:
            pdf_name = vals[0]
            name = vals[1]
            thread_count = vals[2]
            figures = []
            p_name = pdf_name.replace("My Passport", "My\ Passport")
            num_pages = int(subprocess.check_output(
                f"pdfinfo {p_name} | grep -a Pages | sed 's/[^0-9]*//'",
                shell=True,
                encoding="UTF-8"))

            if num_pages > 15:  # skip all the documents that have less than 15 pages
                images = convert_from_path(
                    pdf_name, dpi=72, thread_count=thread_count)
                imgs = [np.array(image) for image in images]

                landscape_c = 0
                for img in imgs:
                    if img.shape[1] > img.shape[0]:
                        landscape_c += 1

                masks = []
                new_imgs = []

                for page_num, img in enumerate(imgs):
                    new_orig, mask = Figures.remove_images(img)
                    new_imgs.append(new_orig)
                    masks.append(mask)

                new_imgs, masks = Figures.remove_headers(
                    new_imgs, masks, num_pages)
                new_imgs = [np.flipud(img) for img in new_imgs]
                masks = [np.flipud(mask) for mask in masks]
                new_imgs, masks = Figures.remove_headers(
                    new_imgs, masks, num_pages)  # same just for footers
                new_imgs = [np.flipud(img) for img in new_imgs]
                masks = [np.flipud(mask) for mask in masks]
                for ind, mask in enumerate(masks):
                    contours = cv2.findContours(
                        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
                    contours.sort(key=lambda c: cv2.boundingRect(c)[1])
                    coords = []
                    for cnt in contours:
                        x, y, w, h = cv2.boundingRect(cnt)
                        if h > 2:
                            coords.append([y, h])
                    figures.append(coords)
                d = {"id": f'{name.replace(".pdf", "")}',
                     "figures": figures, "status": True, "error": ""}
                with open(f'./figures/{name.replace(".pdf", ".txt")}', "w") as f:
                    # skip if half the pages are in landscape
                    if landscape_c > len(imgs) // 2:
                        d = {"id": f'{name.replace(".pdf", "")}', "figures": figures, "status": True,
                             "error": "This PDF had more than half pages in landscape."}
                    values = json.dumps(d)
                    f.write(values)

            else:
                d = {"id": f'{name.replace(".pdf", "")}', "figures": figures,
                     "status": False, "error": "This PDF had less than 15 pages."}
                with open(f'./figures/{name.replace(".pdf", ".txt")}', "w") as f:
                    values = json.dumps(d)
                    f.write(values)
        except:
            pass

    @staticmethod
    def remove_headers(new_imgs, masks, num_pages):
        template1 = Figures.make_template(new_imgs, num_pages)
        template2 = Figures.make_template(new_imgs, num_pages, odd=True)
        if template1 is not None:
            headers_even = Figures.check_similarity(template1, new_imgs)
        else:
            headers_even = [0 for _ in range(len(new_imgs))]
        if template2 is not None:
            headers_odd = Figures.check_similarity(template2, new_imgs)
        else:
            headers_odd = [0 for _ in range(len(new_imgs))]

        all_headers = []
        if len(headers_even) == len(headers_odd):
            for a, b in zip(headers_odd, headers_even):
                if a == 1 or b == 1:
                    header = 1
                else:
                    header = 0
                all_headers.append(header)
        elif len(headers_even):
            all_headers = headers_even
        elif len(headers_odd):
            all_headers = headers_odd

        template = None
        template_h = 0
        if template1 is not None:
            template = template1
        elif template2 is not None:
            template = template2

        if template is not None:
            template_h = template.shape[0]

        if template_h:
            for page_num, img in enumerate(new_imgs):
                if all_headers[page_num]:
                    mask = masks[page_num].copy()
                    w = mask.shape[1]
                    img = img.copy()
                    masks[page_num] = cv2.rectangle(
                        mask, (0, 0), (w, template_h), (0, 0, 0), -1)
                    new_imgs[page_num] = cv2.rectangle(
                        img, (0, 0), (w, template_h), (255, 255, 255), -1)
        return new_imgs, masks

    @staticmethod
    def header(imgs, ind1, ind2):
        found_header = False
        img1 = imgs[ind1].copy()
        img2 = imgs[ind2].copy()
        d1 = 4
        d2 = 4
        x3, y3, w3, h3 = 0, 0, 0, 0
        while img1.shape[0] < img1.shape[1]:
            try:
                img1 = imgs[ind1 + d1]
                d1 += 2
            except IndexError:
                img1 = None
        while img2.shape[0] < img2.shape[1]:
            try:
                img2 = imgs[ind2 + d2]
                d2 += 2
            except IndexError:
                img2 = None
        if img1 is not None and img2 is not None:
            if img1.shape[0] == img2.shape[0] and img1.shape[1] == img2.shape[1]:
                img1 = img1[0:img1.shape[0]//4, 0:img1.shape[1]]
                img2 = img2[0:img2.shape[0]//4, 0:img2.shape[1]]
                diff = cv2.absdiff(img2, img1)

                gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
                kernel = np.ones((5, img1.shape[1]), np.uint8)

                closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

                contours = cv2.findContours(
                    closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
                x3, y3, w3, h3 = None, None, None, None
                if len(contours):

                    for cnt in contours:
                        x1, y1, w1, h1 = cv2.boundingRect(cnt)
                        cv2.rectangle(img1, (x1, y1),
                                      (x1 + w1, y1 + h1), (255, 255, 255), -1)

                    gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.threshold(
                        gray, 254, 255, cv2.THRESH_BINARY_INV)[1]

                    kernel = np.ones((25, img1.shape[1]), np.uint8)
                    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                    contours = cv2.findContours(
                        closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]

                    if len(contours):
                        cnt = max(contours, key=lambda c: cv2.contourArea(c))
                        x3, y3, w3, h3 = cv2.boundingRect(cnt)
                        if y3+h3 < 60:
                            img1 = img1[0:y3 + h3 + 10, 0:img1.shape[1]].copy()
                            found_header = True
                    else:
                        img1 = img1[0:img1.shape[0] // 4, 0:img1.shape[1]]
                else:
                    img1 = img1[0:img1.shape[0] // 4, 0:img1.shape[1]]
        return img1, found_header, [x3, y3, w3, h3]

    @staticmethod
    def make_template(imgs, num_pages, odd=False):
        template = None
        ind1 = 13 if num_pages < 35 else 23
        ind2 = 15 if num_pages < 35 else 25
        if odd:
            ind1 -= 1
            ind2 -= 1
        img1 = imgs[ind1].copy()
        img2 = imgs[ind2].copy()
        d1 = 4
        d2 = 4
        if img1 is not None and img2 is not None:
            while img1 is not None and img1.shape[0] < img1.shape[1]:
                try:
                    img1 = imgs[ind1 + d1]
                    d1 += 2
                except IndexError:
                    img1 = None
            while img2 is not None and img2.shape[0] < img2.shape[1]:
                try:
                    img2 = imgs[ind2 + d2]
                    d2 += 2
                except IndexError:
                    img2 = None

            if img1 is not None and img2 is not None and img1.shape[0] == img2.shape[0] and img1.shape[1] == img2.shape[1]:
                img1 = img1[0:130, 0:img1.shape[1]]
                img2 = img2[0:130, 0:img2.shape[1]]
                diff = cv2.absdiff(img1, img2)
                diff = diff[0:130, 0:img1.shape[1]]
                gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
                kernel = np.ones((10, 25), np.uint8)
                closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                contours = cv2.findContours(
                    closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]

                new = img1.copy()
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w > 20:
                        cv2.rectangle(new, (x, y-1), (x+w, y+h+1),
                                      (255, 255, 255), -1)
                gray = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(
                    gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
                kernel = np.ones((10, 25), np.uint8)
                closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                contours = cv2.findContours(
                    closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
                if len(contours):
                    cnt = max(contours, key=lambda c: cv2.contourArea(c))
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w > 30:
                        template = img1[0:y+h+10, 0:img1.shape[1]]

        if template is not None:
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
            white = cv2.countNonZero(thresh)
            if white < 300:
                template = None
        return template

    @staticmethod
    def remove_images(img):
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
        kernel = np.ones((1, 2*w), np.uint8)
        closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((30, 1), np.uint8)
        opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
        contours = cv2.findContours(
            opening, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        contours.sort(key=lambda c: cv2.boundingRect(c)[1])
        new_orig = img.copy()
        mask = np.ones((img.shape[:2]), dtype=np.uint8)*255
        if len(contours):
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                new_orig = cv2.rectangle(
                    new_orig, (x, y), (x+w, y+h), (255, 255, 255), -1)
                mask = cv2.rectangle(mask, (x, y), (x+w, y+h), (0, 0, 0), -1)
        return new_orig, mask

    @staticmethod
    def check_similarity(template, imgs):
        t_h, t_w = template.shape[:2]
        headers = []
        for page_num, img in enumerate(imgs):
            img = img[0:t_h, 0:t_w]
            sift = cv2.SIFT_create()
            kp1, des1 = sift.detectAndCompute(img, None)
            kp2, des2 = sift.detectAndCompute(template, None)
            bf = cv2.BFMatcher()
            try:
                matches = bf.knnMatch(des1, des2, k=2)
            except:
                matches = 0
            good = []
            try:
                for m, n in matches:
                    if m.distance < 10 * n.distance:
                        good.append([m])
            except:
                pass
            a = len(good)
            if len(kp2):
                percent = (a * 100) / len(kp2)
            else:
                percent = 0

            if percent > 55:
                headers.append(1)
            else:
                headers.append(0)
        return headers


base_name = "./PDF"
all_pdfs = []


for path, subdirs, files in os.walk(base_name):
    for name in files:
        if name.endswith(".pdf"):
            all_pdfs.append([name, os.path.join(path, name)])

all_pdfs = natsorted(all_pdfs, reverse=True)
num_files = len(all_pdfs)


args = []
funcs = []
for name_list in all_pdfs:
    name = name_list[0]
    pdf_name = name_list[1]
    args.append([pdf_name, name, 1])
    pdf = Figures(pdf_name, name, 1)
    funcs.append(pdf)

cpu_count = os.cpu_count() - 1 if os.cpu_count() > 1 else 1
with multiprocessing.Pool(cpu_count) as p:
    r = list(tqdm.tqdm(p.imap_unordered(Figures.main, args), total=len(funcs)))


BASE_DIR = "./figures"
files = [os.path.join(BASE_DIR, f) for f in os.listdir(
    BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f)) and f.endswith(".txt")]

temp = "["
for j, i in enumerate(files):
    with open(i, "r") as f:
        dict_ = f.read()

        if j != len(files) - 1:
            temp = temp + dict_ + "," + "\n"
        else:
            temp = temp + dict_
temp = temp + "]"

with open("./figures.jsonl", "w") as f:
    f.write(temp)

for file in files:
    os.remove(file)

figs = pd.read_json("figures.jsonl")
figs.to_csv("./figures/figures.csv", sep="|")
# os.remove("./figures.jsonl")
