import os
import cv2

def get_scale():
    h, w = working_image.shape[:2]
    scale = 720.0 / max(w, h)
    return scale

def show_annos():
    show_img = working_image.copy()
    h, w = show_img.shape[:2]
    scale = get_scale()
    std_img = cv2.resize(show_img, (int(w*scale), int(h*scale)))
    for index, anno in enumerate(annos):
        x, y, r = anno
        cv2.circle(std_img,(int(x*scale),int(y*scale)),int(r*scale),(255,0,0) if index==len(annos)-1 else (0,0,255),3)
    cv2.imshow('anno', std_img)
    cv2.waitKey(1)

def pick_one_hot(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDOWN:
        scale = get_scale()
        annos.append([int(x/scale),int(y/scale),int(60.0/scale)])
        show_annos()
        
DIR = './Images'
ANNO_FILE = './anno.csv'
show_annotations = True
with open(ANNO_FILE, 'r') as f:
    lines = f.readlines()
    if show_annotations:
        for line in lines:
            elems = line.strip().split(',')
            if len(elems) > 1:
                image = cv2.imread(os.path.join(DIR, elems[0]))
                h, w = image.shape[:2]
                scale = 720.0 / max(w, h)
                show_image = cv2.resize(image, (int(w*scale), int(h*scale)))
                for cir in elems[1:]:
                    x, y, r = cir.split('_')
                    x = int(float(x) * scale)
                    y = int(float(y) * scale)
                    r = int(float(r) * scale)
                    cv2.circle(show_image, (x, y), r, (255,0,0), 3)

                cv2.imshow('show', show_image)
                c = cv2.waitKey(0)
                if c & 0xFF == 27:
                    exit(0)

    annoed_images = [line.split('jpg')[0] + 'jpg' for line in lines]

cv2.namedWindow('anno')
cv2.setMouseCallback('anno',pick_one_hot)
working_image = None
annos = []


for filename in os.listdir(DIR):
    if filename in annoed_images:
        continue

    image_path = os.path.join(DIR, filename)
    image = cv2.imread(image_path)
    if image is None:
        continue
    working_image = image.copy()
    show_annos()
    
    while(1):
        c = cv2.waitKey(0)
        # Esc to exit
        if c & 0xFF == 27:
            exit(0)
        # Space to next image
        if c & 0xFF == 32:
            with open(ANNO_FILE, 'a+') as anno_file:
                anno_file.write("%s" % filename)
                for anno in annos:
                    x, y, r = anno
                    anno_file.write(",%d_%d_%d" % (x, y, r))
                anno_file.write('\n')

            annos = []
            break
        # r to reset
        if c & 0xFF == 114:
            annos = []
        # d to decrease
        if c & 0xFF == 100:
            if len(annos) > 0:
                annos[len(annos)-1][2] += 2
        # f to decrease
        if c & 0xFF == 102:
            if len(annos) > 0:
                annos[len(annos)-1][2] -= 1
        show_annos()
