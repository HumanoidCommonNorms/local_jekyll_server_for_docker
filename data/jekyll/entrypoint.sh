#!/bin/bash
set +ue
SERVER_IP=${SERVER_IP:-$(hostname -I | cut -f1 -d' ')}
SERVER_PORT=${EXPOSE_PORT:-8000}
PRINT_SCRIPT=${PRINT_SCRIPT:-false}
ret=1

if [ "$PRINT_SCRIPT" = "false" ]; then
    pushd /root/jekyll > /dev/null
        rm -rf /root/_site/*

        bundle exec jekyll build \
                --config /root/jekyll/_config.yml,/root/src/_config.yml

        echo "======================================================"
        echo "Build time: $(TZ=UTC date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
        if test -e "/root/_site/index.html";then
            #echo "Internal IP:$SERVER_IP"
            echo "[INFO] Open this link in your browser: http://localhost:${SERVER_PORT}"
            echo "======================================================"
            bundle exec jekyll serve \
                --no-watch \
                --config /root/jekyll/_config.yml,/root/src/_config.yml \
                --quiet \
                --host ${SERVER_IP} --port ${SERVER_PORT}
            ret=0
        else
            echo "[ERROR] Failed to build site"
            echo "======================================================"
        fi
    popd > /dev/null
fi

export PRINT_SCRIPT=true
exit ${ret}
