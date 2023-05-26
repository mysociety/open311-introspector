build:
	date > version.txt
	git rev-parse HEAD >> version.txt
	docker build  -t davea/introspector:latest .
	rm version.txt

publish: build
	docker push davea/introspector:latest
