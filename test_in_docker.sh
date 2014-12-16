#!/bin/sh -x
env
docker ps

mongo_container_id=$(docker run -d --name mongodb_webhooks_test${BUILD_NUMBER} -p 27017:27017 -v /tmp/mongodb${BUILD_NUMBER}:/data/db dockerfile/mongodb mongod --smallfiles)
sleep 10
docker ps
docker logs ${mongo_container_id}

docker run --rm --link mongodb_webhooks_test${BUILD_NUMBER}:mongodb -e MONGO_DB_HOST=mongodb dataxu/github-webhooks python webhooks_test.py
result=$?

docker stop mongodb_webhooks_test${BUILD_NUMBER}
docker rm mongodb_webhooks_test${BUILD_NUMBER}
exit $result
