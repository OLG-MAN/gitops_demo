### GitOps DEMO 

<strong>Infrastructure</strong> - WSL2/Docker-desktop + [kind](https://kind.sigs.k8s.io/docs/user/using-wsl2/) cluster\
<strong>CI/CD tools</strong> - GitHub Actions, [FluxCD](https://fluxcd.io/flux/get-started/), ArgoCD\
<strong>OCI</strong> - Kind local registry, DockerHub, GHCR, Helm Charts.\
<strong>Monitoring</strong> - Prometheus, Grafana, Loki.

#### Demo Steps

##### Install, Bootstrap Steps

```
# WSL2 OPTION
# Installing kind on WSL2 (Windows 11), 
# Docker already pre-installed https://docs.docker.com/install/

curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind
mv ./kind /usr/local/bin/kind
kind version
```

```
# Windows 11 OPTION with docker-desktop 

curl.exe -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.22.0/kind-windows-amd64
Move-Item .\kind-windows-amd64.exe c:\some-dir-in-your-PATH\kind.exe
```

```
# Start kind cluster

# WSL2 option
kind create cluster --name demo --config=cluster-config.yml

# Docker-desktop option (Powershell)
kind create cluster --name demo --config=cluster-config.yml
```

```
# Start working container wifor interaction with kind cluster (For Docker-desktop option)
docker run -it --rm -v ${HOME}:/root/ -v ${PWD}:/git -w /git --net host olegan/work-container:v2.8
```

```
# Test cluster with Nginx 
kubectl get nodes -o wide 
kubectl create deployment nginx --image=nginx --port=80
kubectl create service nodeport nginx --tcp=80:80 --node-port=30000
curl localhost:30000
```

```
# Install FluxCD
curl -o /tmp/flux.tar.gz -sLO https://github.com/fluxcd/flux2/releases/download/v2.2.3/flux_2.2.3_linux_amd64.tar.gz
tar -C /tmp/ -zxvf /tmp/flux.tar.gz
mv /tmp/flux /usr/local/bin/flux
chmod +x /usr/local/bin/flux
# OR
curl -s https://fluxcd.io/install.sh | bash

# And make pre=check
flux --version
flux check --pre
```
 
```
# Bootstrap FluxCD with 'gitops_demo' repository (monorepo approach)

flux bootstrap github \
  --token-auth \
  --owner=OLG-MAN \
  --repository=gitops_demo \
  --branch=main \
  --path=./flux-clusters/demo-cluster \
  --personal
```

##### Git Source with Flux (base doc example)

```
flux create source git podinfo \
  --url=https://github.com/stefanprodan/podinfo \
  --branch=master \
  --interval=1m \
  --export > ./flux-clusters/demo-cluster/podinfo-source.yaml
```

##### Kustomization with Flux (apply pod info app, base example)
```
flux create kustomization podinfo \
  --target-namespace=default \
  --source=podinfo \
  --path="./kustomize" \
  --prune=true \
  --wait=true \
  --interval=30m \
  --retry-interval=2m \
  --health-check-timeout=3m \
  --export > ./flux-clusters/demo-cluster/podinfo-kustomization.yaml
```

##### Build and push image for monorepo-app-1
```
# Build app with Docker (on Win11)
docker build -t monorepo-app-1:0.0.1 ./apps/monorepo-app-1/src

# Load the image to our demo kind cluster
kind load docker-image monorepo-app-1:0.0.1 --name demo
```

##### Apply app infra with flux for monorepo-app-1
```
# applying flux get source and kustomization
kubectl apply -f ./apps-infra/monorepo-app-1/gitrepository.yaml
kubectl apply -f ./apps-infra/monorepo-app-1/kustomization.yaml
```

##### Update/Build/push monorepo-app-1
```
# Change app version in app.py and deployment.yaml files
--- ./apps/monorepo-app-1/src/app.py
--- ./apps/monorepo-app-1/deploy/deployment.yaml

# Build app with Docker (on Win11)
docker build -t monorepo-app-1:0.0.2 ./apps/monorepo-app-1/src

# Load the image to our demo kind cluster
kind load docker-image monorepo-app-1:0.0.2 --name demo

# Commit and push changes to the repo
git add .
git commit  -m "Update monorepo-app-1 to 0.0.2"
git push

# Check the app in the cluster
kubectl get all
```

##### Using image controller approach for CD (Auto deploy by scanning image registry)

```
# Re-bootsrap FluxCD with image controller
flux bootstrap github \
  --token-auth \
  --owner=OLG-MAN \
  --repository=gitops_demo \
  --branch=main \
  --path=./flux-clusters/demo-cluster \
  --components-extra=image-reflector-controller,image-automation-controller \
  --personal

# Deploy a secret with DockerHub credentials (If your imagerepository not public) e.g.:
kubectl -n default create secret docker-registry dockerhub-credential --docker-username '' --docker-password '' --docker-email 'test@test.com'
```

```
# Build and push monorepo-app-2 to DockerHub
docker build -t olegan/monorepo-app-2:0.0.1 ./apps/monorepo-app-2/src
docker push olegan/monorepo-app-2:0.0.1

# Create a secret for github repo push
flux -n default create secret git monorepo-app-2-git-deploy --url=ssh://git@github.com/OLG-MAN/gitops_demo.git

# Copy value and paste to deploy keys in target github repo settings
# Check "Allow write access" and add deploy key
```

```
# Apply main flux objects
kubectl apply -f ./apps-infra/monorepo-app-2/gitrepository.yaml
kubectl apply -f ./apps-infra/monorepo-app-2/kustomization.yaml

# Apply image controller objects
kubectl apply -f ./apps-infra/monorepo-app-2/imagerepository.yaml
kubectl apply -f ./apps-infra/monorepo-app-2/imagepolicy.yaml
kubectl apply -f ./apps-infra/monorepo-app-2/imageupdateautomation.yaml
```

```
# Make application changes and rebuild + push
docker build -t olegan/monorepo-app-2:0.0.2 ./apps/monorepo-app-2/src
docker push olegan/monorepo-app-2:0.0.2

# Check changes in flux image controller objects
kubectl describe imagerepository
kubectl describe imagepolicy monorepo-app-2
kubectl describe imageupdateautomation monorepo-app-2

flux -n default get all
kubectl get all
```
