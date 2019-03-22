# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
source "$script_dir/../scripts/colorecho.sh"

function usage {
    echo "  $0 [lang]"
    echo "  example: $0 node"
    echo ""
    echo "lang can be one of [node, csharp, c, java, python, pythonpreview]"
    echo ""
}

language="$1"
case $language in
    python)
        swagger_language=python-flask
        ;;
    pythonpreview)
        swagger_language=python-flask
        ;;
    java)
        swagger_language=java-vertx
        ;;
    c)
        swagger_language=restbed
        ;;
    csharp)
        swagger_language=aspnetcore
        ;;
    node)
        swagger_language=nodejs-server
        ;;
    *)
        colorecho _red "Unkonwn language: $(language)"
        usage
        exit 1
        ;;
esac

colorecho $_yellow "Generating wrappers for ${language} using ${swagger_language} generator"

docker run --rm -v ${script_dir}:/local swaggerapi/swagger-codegen-cli generate \
    -i /local/v2/e2e-restapi.yaml \
    -l $swagger_language \
    -o /local/swagger_generated/${language}/
if [ $? -ne 0 ]; then
    colorecho $_red "docker run returned failure"
    exit 1
else
    colorecho $_green "success.  generated files are at ${script_dir}/swagger_generated/${language}"
fi

