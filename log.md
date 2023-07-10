# 요괴

## 제작 배경

현재 폐쇄 회로형 감시 카메라(CCTV)는 훌륭한 역할을 수행하고 있지만 한계점은 명확히 존재했습니다. 고정된 위치에 배치되어 사각지대가 생길 가능성이 높으며, CCTV의 위치가 드러나어 증거 인멸로 CCTV를 파손하고 저지르는 행위등이 일어나고 있습니다. 이런 행위를 방지, 그리고 범죄를 예방하기 위하여 이동식 CCTV의 필요성을 느꼈습니다.

그러던 와중에 제가 즐겨하던 게임 'Rainbow Six Siz' 중 '에코'라는 요원이 들고다니는 이동식 드론이 있는데, 이 드론을 활용하여 이동식 카메라를 만들어보자고 결심했습니다.

## 제작 환경

- IDE : vscode
- Language : Python
  - package : flask, opencv
- H/W : Raspberry Pi 4 B+
  - camera :
  - Motor: 

## 만든 과정

### 1. 영상 스트리밍 서버 만들기

<a href="http://wandlab.com/blog/?p=94" target="__blank">이 글</a>을 참조했습니다!

1. 패키지 설치   
아래 패키지를 설치하면 됩니다!   

```
cython
numpy<17
imutils
flask
opencv-python
opencv-contrib-python
```

2. 먼저 OpenCV를 활용하여 일반 PC Cam을 이용해 비디오 촬영 후 루프백하는 코드를 작성하였습니다.

```python
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
```

3. 그다음 영상 스트리밍을 송출해주는 메인 서버 역할 파일을 만들어줍니다. 스트리밍 기능 파일은 바로 다음에 만듭니다! 전 파일결로를 `Server/server.py`로 잡았습니다.

```python
# server.py

import flask
from flask import request               # GET, POST 메소드 - 파라미터의 값 받음
from flask import Response              # 페이지 데이터 및 콘텐츠 출력 쌔 사용. html, text 등 다양한 웹 콘텐츠 출력 가능
from flask import stream_with_context   # url 호출 시, 접속이 timeout 되는 것과 관계 없이 호출한 내용을 유지시켜 지속적으로 데이터 전송
from Server.streamer import Streamer

app = flask.Flask(__name__)     # flask 서버 호출, __name__ : 현재 패키지 경로 인식

streamer = Streamer()

@app.route('/stream')
def stream():       # URL 호출 시 실행
    
    src = request.args.get('src', default=0, type = int)
    
    try:
        return Response(
            stream_with_context(stream_gen(src)),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e :
        print('[Yokai] ', 'stream error : ', str(e))
        
def stream_gen(src):        # Streamer 클래스의 영상 바이너리 코드를 실시간 처리
    try:
        streamer.run(src)
        
        while True:
            frame = streamer.bytescode()
            yield (b'--frame\r\n'           # Header의 mineType을 multipart/x-mixed-replace 선언
                   b'Content-Type : image/jpeg\r\n\r\n' + frame + b'\r\n')

    except GeneratorExit :                  # Client 접속 종료시 출력
        print('[Yokai]','disconnected stream')
        streamer.stop()

```

4. 영상을 스트리밍 해주는 파일을 만듭니다!

```python
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
            print('[Yokai] ', 'OpenCL Active')
        
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
```

5. 프로젝트 루트 폴더로 올라와 `main.py`를 만들어줍니다. 이름은 상관 없습니다!

```python
from Server.server import app

version = '0.1.0'

if __name__ == '__main__' :
    
    print('-------------------------------')
    print('Yokai - version ' + version)
    print('-------------------------------')
    
    print('\r\nHello User.\r\n')
    
    app.run(host='0.0.0.0', port=5001)
```

실행시키고 `http://localhost:5001`을 주소창에 입력하면 자신의 웹캠이 켜진 웹사이트를 볼 수 있을겁니다.