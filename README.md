# MyGunicorn
나만의 WSGI 서버입니다.
최대한 Gunicorn 처럼 만드는 것이 목표입니다.

## 특징
- 서드파티 라이브러리 NO! 모두 빌트인 라이브러리를 이용(django 제외)
- 멀티 프로세싱과 소켓을 활용
- 워커 개수와 소켓 백로그 개수 조절 가능

## 설치
``` bash
pip install django
pip install djangorestframework
python manage.py migrate
```

## 실행방법
``` bash
python wsgi_server.py
```

## 성능
- 0.1초 단위로 요청 전송
- 동시에 1000명 접속
- worker = 16
- backlog = 1000
### 시험 결과
![시험 결과 이미지](https://fhdufhdu.github.io/post/14/image-8.png)
