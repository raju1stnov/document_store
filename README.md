# document_store
docker-compose down
docker-compose up --build

a. Remove All Stopped Containers
This command removes all containers that are not currently running:
docker container prune -f

b. Remove All Unused Images
This command removes all images that are not used by any containers:
docker image prune -a -f

c. Remove All Unused Volumes
This command removes all volumes that are not referenced by any container:
docker volume prune -f

d. Remove All Unused Networks
This command removes networks not used by any container:
docker network prune -f

e. Remove Everything at Once
If you want to remove all unused containers, images, volumes, and networks in one go, run:
docker system prune -a --volumes -f

2. Removing Specific Containers and Images Manually
If you want more control, you can list and remove containers and images manually.

a. List All Containers
docker ps -a

b. Stop All Running Containers
docker stop $(docker ps -q)

c. Remove All Containers
docker rm $(docker ps -aq)

d. List All Images
docker images -a

e. Remove All Images
Remove images by their IDs (this example removes all images):
docker rmi $(docker images -q)

Sometimes you may need to add the -f flag to force removal:
docker rmi -f $(docker images -q)