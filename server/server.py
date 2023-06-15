import flask
from flask import request               # GET, POST 메소드 - 파라미터의 값 받음
from flask import Response              # 페이지 데이터 및 콘텐츠 출력 쌔 사용. html, text 등 다양한 웹 콘텐츠 출력 가능
from flask import stream_with_context   # url 호출 시, 접속이 timeout 되는 것과 관계 없이 호출한 내용을 유지시켜 지속적으로 데이터 전송
from server.streamer import Streamer

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

    except GeneratorExit :
        print('[Yokai]','disconnected stream')
        streamer.stop()