FROM jfloff/alpine-python:2.7

# for a flask server
ADD . /gcdt
RUN ls -l gcdt
ADD tests/pip.conf /root/.pip/pip.conf
RUN pip install pip-tools
RUN echo 'yugen { slack-token=""}' >> /root/.yugen
RUN echo 'kumo { slack-token=""}' >> /root/.kumo
RUN echo 'ramuda { slack-token=""}' >> /root/.ramuda
WORKDIR /gcdt
RUN ls -l
RUN pip install -U pip==8.1.1
RUN pip-compile
#CMD env && bash install_gcdt.sh
RUN pip-sync
RUN python setup.py install
RUN kumo version && ramuda version && tenkai version && yugen version
