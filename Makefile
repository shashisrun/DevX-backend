install:
	pip install -r requirements.txt
run:
	uvicorn src.main:app --reload
celery:
	celery -A src.services.task_queue.celery_app worker --loglevel=info
build-native:
	./build_native.sh
seed-demo:
	./seed_demo.sh
