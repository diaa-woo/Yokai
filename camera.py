import cv2
import platform

src= 0

if platform.system() == 'Windows' :
    capture = cv2.VideoCapture(src, cv2.CAP_DSHOW)

else :
    capture = cv2.VideoCapture(src)
    
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

while capture.isOpened() :
    (grabbed, frame) = capture.read()
    
    if grabbed :
        cv2.imshow("Yokai Camera Window", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if(key == 27) :
            break
        
capture.release()
cv2.destroyAllWindows()