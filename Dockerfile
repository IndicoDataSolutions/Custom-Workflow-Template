FROM gcr.io/new-indico/numpy-ubuntu:1.15.4 as numpy-base
FROM gcr.io/new-indico/pandas-ubuntu:0.23.4 as pandas-base

FROM gcr.io/new-indico/atmosphere-ubuntu

ARG GITHUB_ACCESS_TOKEN
ARG EXTRAS
ENV APP_NAME custom_app
ENV C_FORCE_ROOT 1

COPY --from=pandas-base /root/.cache/pip/wheels/ /root/.cache/pip/wheels
COPY --from=numpy-base /root/.cache/pip/wheels/ /root/.cache/pip/wheels

RUN pip3 install -U pip

RUN apt-get update && \
    mkdir -p /root/.cache/pip/wheels && \
    install_github_dependencies jetstream && \
    install_github_dependencies celery && \
    install_github_dependencies indicore && \
    install_github_dependencies indico-client-python

ARG INDICORE_TAG=293fe78737dc8a5039614c9c40b827e12aeccaa8
ARG CELERY_TAG=83009c7c22f737eaee351af00bd01339a6421b14
ARG JETSTREAM_TAG=16b8a41b6485fa51d00d2826e2932c0d4b4d14e2
ARG PYTHON_CLIENT_TAG=04aec93b6d0990506cd11318b6ab3c78fe6d785f

RUN update_github_dependencies jetstream ${JETSTREAM_TAG} && \
    update_github_dependencies indicore ${INDICORE_TAG} && \
    update_github_dependencies celery ${CELERY_TAG} && \
    update_github_dependencies indico-client-python ${PYTHON_CLIENT_TAG}

COPY . /custom_app
WORKDIR /custom_app

RUN pip3 install --find-links=/root/.cache/pip/wheels -e .${EXTRAS} && \
    python3 setup.py develop --no-deps && \
    rm -r /root/.cache


CMD ["/custom_app/scripts/entrypoint.sh"]