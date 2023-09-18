.PHONY: up-ita
up-ita:
	docker run \
		--detach \
		--privileged \
		--publish 8080:80 \
		--add-host exastro-it-automation:127.0.0.1 \
		--name test-ita \
		exastro/it-automation:1.11.0-ja


.PHONY: start-ita
start-ita:
	docker start test-ita


.PHONY: stop-ita
stop-ita:
	-docker stop test-ita


.PHONY: down-ita
down-ita: stop-ita
	-docker rm test-ita
