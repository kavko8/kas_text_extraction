import cv2
from pdf2image import convert_from_path
import numpy as np
import tqdm
import os
import subprocess

logf = open("mylogger.txt", "w")


sum_count = tqdm.tqdm(total=91019)
#base_name = "/media/matic/My Passport/pdfji_5000"
base_name = "/media/matic/My Passport/KAS/nl.ijs.si/project/kas/pdf"


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

            contours = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
            x3, y3, w3, h3 = None, None, None, None
            if len(contours):

                for cnt in contours:
                    x1, y1, w1, h1 = cv2.boundingRect(cnt)
                    cv2.rectangle(img1, (x1, y1), (x1 + w1, y1 + h1), (255, 255, 255), -1)

                gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY_INV)[1]

                kernel = np.ones((25, img1.shape[1]), np.uint8)
                closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                contours = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]

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
        img1 = img1[0:130, 0:img1.shape[1]]
        img2 = img2[0:130, 0:img2.shape[1]]
        diff = cv2.absdiff(img1, img2)
        diff = diff[0:130, 0:img1.shape[1]]
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
        kernel = np.ones((10, 25), np.uint8)
        closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]

        new = img1.copy()
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 20:
                cv2.rectangle(new, (x, y-1), (x+w, y+h+1), (255, 255, 255), -1)
        gray = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
        kernel = np.ones((10, 25), np.uint8)
        closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        if len(contours):
            cnt = max(contours, key=lambda c: cv2.contourArea(c))
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 30:
                template = img1[0:y+h+10, 0:img1.shape[1]]

    return template


def remove_images(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
    kernel = np.ones((1, 2*w), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    kernel = np.ones((30, 1), np.uint8)
    opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
    contours = cv2.findContours(opening, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
    contours.sort(key=lambda c: cv2.boundingRect(c)[1])
    new_orig = img.copy()
    bboxes = []
    if len(contours):
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(new_orig, (x-1, y-1), (x+w+1, y+h+1), (255, 255, 255), -1)
            bboxes.append([y, y+h])

    return new_orig, bboxes


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

        # Apply ratio test
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

        # if even[0][0] < 10000 or odd[0][0] < 10000:
        if percent > 55:
            headers.append(1)
        else:
            headers.append(0)
    return headers


def check_numbers(img, orig_img, up=True):
    h, w = img.shape[:2]
    TDLU = [0, 0, 500, 500]
    borderType = cv2.BORDER_CONSTANT

    gray = cv2.cvtColor(img[h-h//3:h], cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
    thresh = cv2.copyMakeBorder(thresh, TDLU[0], TDLU[1], TDLU[2], TDLU[3], borderType,
                                None, 0)
    kernel = np.ones((1, w//2), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    kernel = np.ones((3, 3), np.uint8)
    closing = cv2.morphologyEx(closing, cv2.MORPH_CLOSE, kernel)
    kernel = np.ones((2, 1), np.uint8)
    opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)

    contours = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    new_cut = None

    if len(contours):
        cnt = sorted(contours, key=lambda c: cv2.boundingRect(c)[1], reverse=True)[0]

        c_x, c_y, c_w, c_h = cv2.boundingRect(cnt)
        c_y = c_y - 1
        if c_h < 25 and c_w < 25 and c_y > 3:

            tmp_img = opening[c_y:+c_y+c_h, 0:opening.shape[1]]
            tmp_img[0: tmp_img.shape[0], c_x-1:c_x+c_w+1] = 0
            try:
                white = cv2.countNonZero(tmp_img)
                if not white:
                    img = img[0:h-h//3+c_y]
                    new_cut = h - h // 3 + c_y
                    if not up:
                        new_cut = orig_img.shape[0] - new_cut
            except:
                pass

    return img, new_cut

import pandas as pd

df = pd.DataFrame(columns=["id", "figures"])
df2 = pd.DataFrame(columns=["pass", "fail"])

counter = open("counter.txt", "w")
counter_num = 0
with sum_count as s_c:
    for dir, folder, files in os.walk(base_name):
        for j, name in enumerate(files):
            if name.endswith(".pdf") and "kas-" in name:# and name in files2:
                counter.write(f"{counter_num} - {name}")
                counter.write("\n")
                counter.flush()
                if counter_num > 57072:

                    #print(name)
                    try:
                        pdf_name = os.path.join(dir, name)
                        read_p = True
                        p_name = pdf_name.replace("My Passport", "My\ Passport")
                        num_pages = int(subprocess.check_output(
                            f"pdfinfo {p_name} | grep Pages | sed 's/[^0-9]*//'",  # -y {offset} -H {bottom} -r 72
                            shell=True,
                            encoding="UTF-8"))

                        if num_pages > 19:
                            images = convert_from_path(pdf_name, dpi=72, thread_count=1)  # , last_page=15)
                            imgs = [np.array(image) for image in images]
                            bboxes = []
                            new_imgs = []

                            for page_num, img in enumerate(imgs):
                                new_orig, bbxs = remove_images(img)
                                new_imgs.append(new_orig)
                                bboxes.append(bbxs)
                                #bboxes.append([page_num, bbxs])


                            def remove_headers(new_imgs, imgs, headers=True):
                                template1 = make_template(new_imgs, num_pages)
                                template2 = make_template(new_imgs, num_pages, odd=True)
                                if template1 is not None:
                                    headers_even = check_similarity(template1, new_imgs)
                                else:
                                    headers_even = [0 for _ in range(len(new_imgs))]
                                if template2 is not None:
                                    headers_odd = check_similarity(template2, new_imgs)
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
                                else:
                                    print("Something is wrong at templates")
                                if headers:
                                    position = [0 for i in range(len(imgs))]
                                else:
                                    position = [i.shape[0] for i in imgs]
                                for page_num, img in enumerate(imgs):
                                    if all_headers[page_num]:
                                        if template1 is not None:
                                            if not headers:
                                                position[page_num] = imgs[page_num].shape[0] - (template1.shape[0] - 5)
                                            else:
                                                position[page_num] = template1.shape[0] - 5
                                            new_imgs[page_num] = new_imgs[page_num][template1.shape[0]-5: new_imgs[page_num].shape[0], 0:new_imgs[page_num].shape[1]]
                                        elif template2 is not None:
                                            if not headers:
                                                position[page_num] = imgs[page_num].shape[0] - (template2.shape[0] - 5)
                                            else:
                                                position[page_num] = template2.shape[0] - 5
                                            new_imgs[page_num] = new_imgs[page_num][template2.shape[0]-5: new_imgs[page_num].shape[0], 0:new_imgs[page_num].shape[1]]
                                return all_headers, position

                            headers, headers_position = remove_headers(new_imgs, imgs)
                            new_imgs = [np.flipud(img) for img in new_imgs]
                            footers, footers_position = remove_headers(new_imgs, imgs, False)  # same just for footers
                            new_imgs = [np.flipud(img) for img in new_imgs]


                            for num, img in enumerate(new_imgs):
                                up, down = None, None
                                if headers[num] and footers[num]:
                                    pass
                                elif headers[num] and not footers[num]:
                                    new_imgs[num], down = check_numbers(img, imgs[num])
                                    if headers_position[num] is not None and down is not None:
                                        down = down + headers_position[num]
                                elif not headers[num] and footers[num]:
                                    img = np.flipud(img)
                                    tmp, up = check_numbers(img, imgs[num], False)
                                    img = np.flipud(tmp)
                                    new_imgs[num] = img
                                else:
                                    img_h, img_w = img.shape[:2]
                                    img, down = check_numbers(img, imgs[num])
                                    tmp_h, tmp_w = img.shape[:2]
                                    if img_h == tmp_h and img_w == tmp_w:
                                        tmp = np.flipud(img)
                                        tmp, up = check_numbers(tmp, imgs[num], False)
                                        img = np.flipud(tmp)
                                    new_imgs[num] = img
                                if up is not None:
                                    headers_position[num] = up
                                if down is not None:
                                    footers_position[num] = down

                            def make_list(headers, footers, bboxes):
                                all_coords = []

                                for i in range(len(headers)):

                                    temp = []
                                    temp.append(headers[i])
                                    for bbox in bboxes[i]:
                                        for m in bbox:
                                            temp.append(m)

                                    temp.append(footers[i])
                                    temp2 = []
                                    for k, l in enumerate(temp):
                                        if not k % 2:
                                            if k < len(temp)-1:
                                                temp2.append([l, temp[k+1]-l])
                                    all_coords.append(temp2)
                                return all_coords


                            for number2, (img, img2) in enumerate(zip(imgs, new_imgs)):
                                #hh, ww = img.shape[:2]
                                #hh2, ww2 = img2.shape[:2]
                                #borderType = cv2.BORDER_CONSTANT
                                #mask = np.zeros((img.shape), dtype=np.uint8)
                                #mask[hh-hh2:hh, 0:ww2] = img2
                                #while hh > hh2:
                                #    if hh2 % 2:
                                #        TDLU = [1, 0, 0, 0]  # top,down,left,right values
                                #    else:
                                #        TDLU = [0, 1, 0, 0]
                                #    img2 = cv2.copyMakeBorder(img2, TDLU[0], TDLU[1], TDLU[2], TDLU[3], borderType,
                                #                              None, 0)
                                #    hh2 += 1
                                #cv2.line(img, (ww, 0), (ww, hh), (0, 0, 255), 3)
                                #new = np.hstack([img, mask])
                                #os.makedirs(f"test/{name}", exist_ok=True)
                                #cv2.imwrite(f"./test/{name}/{number2}.png", new)
                                if number2 == 10:
                                    coords = make_list(headers_position, footers_position, bboxes)
                                    df = df.append({
                                        "id": name,
                                        "figures": coords
                                    }, ignore_index=True)
                                    df2 = df2.append({
                                        "pass": name,
                                        "fail": "",
                                    }, ignore_index=True)
                                    read_p = False



                        s_c.update(1)
                        s_c.refresh()

                        ###   cv2.imshow("even", new_imgs[10])
                        #cv2.imshow("odd", header_odd)
                        ###   cv2.waitKey(0)
                        ###   cv2.destroyAllWindows()

                        if read_p:
                            df2 = df2.append({
                                "pass": "",
                                "fail": name,
                            },  ignore_index=True)
                            #logf.write(f"{name}")
                            #logf.write("\n")
                            #logf.flush()
                    except Exception as e:
                        df2 = df2.append({
                            "pass": "",
                            "fail": name,
                        },  ignore_index=True)
                        logf.write(f"{name} {e}")
                        logf.write("\n")
                        logf.flush()

                        #logf.write(f"{pdf_name}: {str(e)}")
                        #logf.write("\n")
                        #logf.flush()
                        s_c.update(1)
                        s_c.refresh()
                else:
                    s_c.update(1)
                    s_c.refresh()
                counter_num += 1
                df.to_csv("./kas_figures.csv", sep="|")
                df2.to_csv("./log.csv", sep="|")
