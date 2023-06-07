# ==================================================================================
#  Copyright (c) 2020 HCL Technologies Limited.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ==================================================================================
FROM frolvlad/alpine-miniconda3:python3.7
# RMR setup
RUN mkdir -p /opt/route/

# copy rmr files from builder image in lieu of an Alpine package
COPY --from=nexus3.o-ran-sc.org:10002/o-ran-sc/bldr-alpine3-rmr:4.0.5 /usr/local/lib64/librmr* /usr/local/lib64/

COPY --from=nexus3.o-ran-sc.org:10002/o-ran-sc/bldr-alpine3-rmr:4.0.5 /usr/local/bin/rmr* /usr/local/bin/
ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64
COPY local.rt /opt/route/local.rt
ENV RMR_SEED_RT /opt/route/local.rt

RUN apk update && apk add gcc musl-dev

# Install
COPY setup.py /tmp
COPY LICENSE.txt /tmp/
# RUN mkdir -p /tmp/ad/
RUN pip install /tmp
RUN pip install ricxappframe
RUN pip install --force-reinstall redis==4.1.1
RUN pip install protobuf==3.20.*
ENV PYTHONUNBUFFERED 1
COPY src/ /src
ENV CONFIG_FILE opt/ric/config/config-file.json
ENV SERVICE_RICXAPP_AD_HTTP_PORT http://noip
ENV SERVICE_RICXAPP_AD_RMR_PORT "http://${AD_IP}:4560"
ENV HOSTNAME ad
CMD PYTHONPATH=/src:/usr/lib/python3.7/site-packages/:$PYTHONPATH run-src.py
