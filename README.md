Start podman:
podman machine init
podman machine start

Run in podman local:
podman build -t decentral . && podman run -it 8000:8000 decentral:v1