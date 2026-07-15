.PHONY: api build-ui install test ui

install:
	python3 -m pip install -r requirements.txt

test:
	PYTHONPATH=core python3 -m unittest discover -s tests

api:
	PYTHONPATH=core uvicorn trusted_data_demo.app:app --host 127.0.0.1 --port 8000 --reload

ui:
	cd ui/demo-console && npm run dev -- --host 127.0.0.1 --port 5173

build-ui:
	cd ui/demo-console && npm run build
