#!/bin/bash
# Clean all containers and images
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker image rm -f $(docker images -q) 2>/dev/null || true
echo "Docker cleaned"

# Reset all terraform states for clean experiment
for d in /home/ject/proyecto/experimento/infra/version_fallo/f{1,2,3,4} /home/ject/proyecto/experimento/infra; do
    cd "$d"
    rm -f terraform.tfstate terraform.tfstate.backup errored.tfstate
    terraform init -no-color 2>&1 | tail -1
done
echo "All terraform states reset"
docker ps -a
