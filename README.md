# Cheatsheet

## Prerequisite
+ [docker]
+ [docker-compose]
+ python 3.7
+ [pipenv]
+ [curl]

## Installation
1. Download ElasticSearch docker image.
    ```sh
    $ docker pull docker.elastic.co/elasticsearch/elasticsearch:7.6.2
    ```
2. Launch the local cluster with 3 nodes using `docker compose`.
    ```sh
    $ docker-compose up
    ```
3. Prepare the Cheatsheet sample installer.
    ```sh
    $ pipenv install --dev
    ```
4. Run the Cheatsheet sample installer and populate the local ElasticSearch cluster.
    ```sh
    $ pipenv run python install.py samples
    ```
5. Verify the installation using simple Elastic query.


    + Check cluster health.
    ```sh
    $ curl http://localhost:9200/
    ```
    + Dump a few samples.
    ```sh
    $ curl http://localhost:9200/_search\?
    ```

[docker]: https://www.docker.com/products/docker-desktop
[docker-compose]: https://docs.docker.com/compose/install/
[pipenv]: https://pipenv-fork.readthedocs.io/en/latest/
[curl]: https://curl.haxx.se/download.html
