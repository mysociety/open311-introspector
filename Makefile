build:
	date > version.txt
	git rev-parse HEAD >> version.txt
	docker build  -t fixmystreet/open311-introspector:latest .
	rm version.txt

publish: build
	docker push fixmystreet/open311-introspector:latest
