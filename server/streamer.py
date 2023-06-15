# Import---------------------------------------
import time
import cv2
import imutils
import platform
import numpy as np
from threading import Thread        # Python의 싱글 스레드를 멀티로 바꿔 OpenCV 및 서버 동시 실행 성능 향상
from queue import Queue             # 처리된 데이터 
#----------------------------------------------

class Streamer:
    
    # Constructor
    def __init__(self):
        
        # OpenCL Active/Deactive part
        print('[Yokai] ', 'OpenCL : ', cv2.ocl.haveOpenCL())        # CPU보다 OpenCL 성능이 더 그래픽 처리 성능이 더 좋기에 만약 해당 PC가 사용시 Active
        if cv2.ocl.haveOpenCL() :
            cv2.ocl.setUseOpenCL(True)
            print('[Yokai] ', 'OpenCL Active')
        else :
            print('[Yokai] ', 'OpenCL Deactive')
        
        # Init Variable
        self.capture = None
        self.thread = None
        self.width = 640
        self.height = 360
        self.stat = False
        self.current_time = time.time()
        self.preview_time = time.time()
        self.sec = 0
        self.Q = Queue(maxsize=128)
        self.started = False
        
    # Streamer Run
    def run(self, src = 0):
        self.stop()
        
        if platform.system() == 'Windows' :     # 이걸 클래스화 시켜줄 순 없을까? 
            self.capture = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        else :
            self.capture = cv2.VideoCapture(src)
            
        if self.thread is None :
            self.thread = Thread(target=self.update, args=())
            self.thread.daemon = False
            self.thread.start()
        
        self.started = True
        
    # Streamer Stop
    def stop(self):
        self.started = False
        
        if self.capture is not None:
            self.capture.release()
            self.clear()
            
    # Streamer Update - 웹캠이 켜지고, 지속적인 프레임 추출
    def update(self):
        while True:
            if self.started :
                (grabbed, frame) = self.capture.read()
                
                if grabbed :
                    self.Q.put(frame)
            
    # Streamer Queue Clear - 큐에 쌓여있는 영상 데이터 삭제
    def clear(self):
        with self.Q.mutex:
            self.Q.queue.clear()
            
    # Streader read - Queue에 쌓여있는 영상 데이터 읽기
    def read(self):
        return self.Q.get()
    
    # Streamer blank - 시스템이 작동하다 frame의 영상 데이터가 없을 경우, 검음 화면 출력
    def blank(self):
        return np.ones(shape=[self.height, self.width, 3], dtype=np.uint8)
    
    # Streamer bytescode - OpenCV 영상을 JPEG 바이너리 변환하여 리턴
    def bytescode(self):
        
        if not self.capture.isOpened():
            frame = self.blank()
        else:
            frame = imutils.resize(self.read(), width=int(self.width))
            
            if self.stat:
                cv2.rectangle(frame, (0,0), (120, 30), (0,0,0), -1)
                fps = 'FPS : ' + str(self.fps())
                cv2.putText(frame, fps, (10, 20), cv2.FONT_HERSHEY_PLAIN)
                
        return cv2.imencode('.jpg',frame)[1].tobytes()
    
    # Streamer FPS - FPS 계산, 출력은 bytecode에서 진행
    def fps(self):
        self.current_time = time.time()
        self.sec = self.current_time - self.preview_time
        
        self.preview_time = self.current_time
        
        if self.sec > 0:
            fps = round(1/(self.sec), 1)
        else :
            fps = 1
        
        return fps
    
    def __exit__(self):
        print("[Yokai] Closed Streamer. Bye.")