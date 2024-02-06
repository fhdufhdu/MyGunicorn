# MyGunicorn
나만의 WSGI 서버입니다.
최대한 Gunicorn 처럼 만드는 것이 목표입니다.

## 특징
- 서드파티 라이브러리 NO! 모두 빌트인 라이브러리를 이용(django 제외)
- 멀티 프로세싱과 소켓을 활용
- 워커 개수와 소켓 백로그 개수 조절 가능

## 설치
```
pip install django
pip install djangorestframework
python manage.py migrate
```

## 실행방법
``` python
python wsgi_server.py
```
