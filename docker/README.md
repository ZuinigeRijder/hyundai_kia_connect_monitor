# Run hyundai_kia_connect_monitor in a Docker container 
If you want to run hyundai_kia_connect_monitor in a Docker container, use the 
files in this directory. The `Dockerfile` assumes that the monitor code is in 
the subdirectory `hyundai_kia_connect_monitor`, so if you cloned this repository
the standard way, it should be copied to `../..`. The Docker-Compose file 
`compose.yaml` shall be in the same direcory. It assumes that the cfg- and 
csv-files go into the same directory. You may need to create them first, for 
example with `touch monitor.csv`.

If you are not familiar with Docker, see the [Docker Compose Quickstart](https://docs.docker.com/compose/gettingstarted/) for an introduction to `docker compose` and a guide to the commands required.

