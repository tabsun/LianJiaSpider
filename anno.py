import os
import cv2

def show_annos():
    show_img = working_image.copy()
    for index, anno in enumerate(annos):
        x, y, r = anno
        cv2.circle(show_img,(x,y),r,(255,0,0) if index==len(annos)-1 else (0,0,255),3)
    cv2.imshow('anno', show_img)
    cv2.waitKey(1)

def pick_one_hot(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDOWN:
        annos.append([x,y,10])
        show_annos()
        
DIR = './Images'

cv2.namedWindow('anno')
cv2.setMouseCallback('anno',pick_one_hot)
working_image = None
annos = []


for filename in os.listdir(DIR):
    image_path = os.path.join(DIR, filename)
    image = cv2.imread(image_path)
    working_image = image.copy()

    cv2.imshow("anno", image)
    
    while(1):
        c = cv2.waitKey(0)
        print c & 0xFF
        # Esc to exit
        if c & 0xFF == 27:
            exit(0)
        # Space to next image
        if c & 0xFF == 32:
            with open('anno.csv', 'a+') as anno_file:
                anno_file.write("%s" % filename)
                for anno in annos:
                    x, y, r = anno
                    anno_file.write(",%d_%d_%d" % (x, y, r))
            annos = []
            break
        # r to reset
        if c & 0xFF == 114:
            annos = []
        # d to decrease
        if c & 0xFF == 100:
            if len(annos) > 0:
                annos[len(annos)-1][2] += 1
        # f to decrease
        if c & 0xFF == 102:
            if len(annos) > 0:
                annos[len(annos)-1][2] -= 1
        show_annos()
