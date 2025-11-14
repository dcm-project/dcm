podman run -p 8080:8080 -e SWAGGER_JSON=/data/v2.100.yaml -v $PWD:/data:z docker.swagger.io/swaggerapi/swagger-ui
