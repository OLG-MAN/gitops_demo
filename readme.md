### GitOps DEMO 

<strong>Infrastructure</strong> - WSL2/Docker-desktop + [kind](https://kind.sigs.k8s.io/docs/user/using-wsl2/) cluster\
<strong>CI/CD tools</strong> - GitHub Actions(TBD), [FluxCD](https://fluxcd.io/flux/get-started/), ArgoCD(TBD)\
<strong>OCI</strong> - Kind local registry, DockerHub, GHCR, Helm Charts.\
<strong>Monitoring(TBD)</strong> - Prometheus, Grafana, Loki.

#### Demo Steps

##### Install, Bootstrap Steps

```
# WSL2 OPTION
# Installing kind on WSL2(Windows 11), 
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
# Start working container for interaction with kind cluster (WSL2 option)
docker run -it --rm -v $HOME:/root/ -v $PWD:/git -w /git --net host olegan/work-container:v2.8

# Start working container for interaction with kind cluster (For Docker-desktop option)
docker run -it --rm -v ${HOME}:/root/ -v ${PWD}:/git -w /git --net host olegan/work-container:v3.0
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

# DO NOT forget pull your repo after bootstrap/reconcilation
```

##### Monorepo app 1 (declarative way)
##### Git repository source approach for CD (Auto deploy by scanning git repo)
```
# Build app with Docker (on Win11)
docker build -t monorepo-app-1:0.0.1 ./apps/monorepo-app-1/src

# Load the image to our demo kind cluster
kind load docker-image monorepo-app-1:0.0.1 --name demo
```

##### Apply app infra with flux for monorepo-app-1
```
# Applying flux git source and kustomization
kubectl apply -f ./apps-infra/monorepo-app-1/gitrepository.yaml
kubectl apply -f ./apps-infra/monorepo-app-1/kustomization.yaml

# Check app in kind cluster
kubectl get all
flux -n default get all
```

##### Update/Build/Push monorepo-app-1
```
# Change app version in app.py and deployment.yaml files
--- ./apps/monorepo-app-1/src/app.py
--- ./apps/monorepo-app-1/deploy/deployment.yaml

# Re-Build new app version with Docker (on Win11)
docker build -t monorepo-app-1:0.0.2 ./apps/monorepo-app-1/src

# Load the image to our demo kind cluster
kind load docker-image monorepo-app-1:0.0.2 --name demo

# Commit and push changes to the repo for flux CD automation
git add .
git commit  -m "Update monorepo-app-1 to 0.0.2"
git push

# Check the new app version in the kind cluster
kubectl get all
```

##### Monorepo app 2 (declarative way)
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

watch flux -n default get all
watch kubectl get all
```

##### Separate repo app 1: helm-git-app (imperative way)
##### Using Helm chart approach for CD (Auto deploy by scanning Helm chart in git repo)

```
# Build and push app with Docker (on Win11)
docker build -t olegan/helm-git-app:0.0.1 ./src
docker push olegan/helm-git-app:0.0.1

# Creating git source with Helm chart
flux create source git helm-git-app \
  --url=https://github.com/OLG-MAN/gitops_demo_app \
  --branch=helm-git-app \
  --namespace=default \
  --timeout=1m   \
  --export > ./apps-infra/helm-git-app/gitrepository.yaml


# Creating Helm Release for app based on git repo source
flux create hr helm-git-app \
  --release-name=helm-git-app \
  --namespace=default \
  --source=GitRepository/helm-git-app \
  --chart=helm-chart \
  --interval=1m \
  --timeout=1m \
  --export > ./apps-infra/helm-git-app/helmrelease.yaml

# Checking app
kubectl get all
curl localhost:30003
```

```
# Build and push 2nd app with Docker (on Win11)
docker build -t olegan/helm-git-app:0.0.2 ./src
docker push olegan/helm-git-app:0.0.2

# Create 2nd Helm Release based on same git source
# but with our local changed values from flux infra repo
flux create hr helm-git-app2 \
  --release-name=helm-git-app2 \
  --namespace=default \
  --target-namespace=default \
  --source=GitRepository/helm-git-app \
  --chart=helm-chart \
  --values=./apps-infra/helm-git-app/values.yaml \
  --interval=1m \
  --timeout=1m \
  --export > ./apps-infra/helm-git-app/helmrelease2.yaml

# Checking app
kubectl get all
curl localhost:30004
```

##### Separate repo app 2: helm-repo-app (imperative way)
##### Using Helm repo / Artifact Hub approach for CD (Auto deploy by scanning Helm repo)

```
# Build and push app with Docker (on Win11)
docker build -t olegan/helm-repo-app:0.0.1 ./src
docker push olegan/helm-repo-app:0.0.1

# Install Helm (if need)
curl -fsSL -o /git/get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 /git/get_helm.sh
/git/get_helm.sh

# Creating Helm Repository (based on GitHub pages)
helm package ./helm-chart/
helm repo index --url  https://olg-man.github.io/gitops_demo_app/ .
# Push changes to repo
# Create a GitHub pages by `helm-repo-app` branch

# (optionally)
# Create a repo on ArtifactHub, link it to the Github pages 
# Create a artifacthub-repo.yml metadata with needed values from ArtifactHub
# Push changes to repo
```

```
# Creating Helm repo source 
flux create source helm helm-repo-app \
  --url=https://olg-man.github.io/gitops_demo_app/ \
  --namespace=default \
  --interval=1m \
  --export > ./apps-infra/helm-repo-app/helmrepository.yaml

# Creating Helm Release for app based on Helm repo source
flux create hr helm-repo-app \
  --release-name=helm-repo-app \
  --namespace=default \
  --target-namespace=default \
  --source=HelmRepository/helm-repo-app \
  --chart=helm-repo-app \
  --interval=1m \
  --export > ./apps-infra/helm-repo-app/helmrelease.yaml

# Checking app
kubectl get all
curl localhost:30005
```

##### Separate repo app 3: gchr-app (imperative way)
##### Using GHCR repo approach for CD (Auto deploy by scanning GHCR repo)

```
# Pre-Build and push app with Docker (on Win11)
docker build -t olegan/ghcr-app:0.0.1 ./src
docker push olegan/ghcr-app:0.0.1

# Checking our GH token and update if need with `delete:packages, repo, user, write:packages` permissions.

# Workaround to login and push artifact in case of multiple envs (e.g. win11/docker-desktop and working docker container) 
# Login and push artifact from repo to ghcr.io (from win11/docker-descktop)
docker login ghcr.io -u olg-man

# Flux command for Powershell 
flux push artifact oci://ghcr.io/olg-man/ghcr-app:0.0.1-$((git rev-parse --short HEAD)) --path=".\manifests" --source="$(git config --get remote.origin.url)" --revision="$(git branch --show-current)@sha1:$(git rev-parse HEAD)"

# Push to ghcr.io (for WSL or linux container, not used during this guide only as FYI) 
flux push artifact oci://ghcr.io/olg-man/ghcr-app:0.0.1-$(git rev-parse --short HEAD) \
  --path="./manifests" \
  --source="$(git config --get remote.origin.url)" \
  --revision="$(git branch --show-current)@sha1:$(git rev-parse HEAD)"
```

```
# Create an OCI source in flux
flux create source oci ghcr-app \
  --url=oci://ghcr.io/olg-man/ghcr-app \
  --namespace=default \
  --tag=0.0.1-d514bc2 \
  --export > ./apps-infra/ghcr-app/ocisource.yaml

# (Optional) Create a secret if oci source is private
flux create secret oci ghcr-app \
  --container-registry ghcr.io \
  --username <user-name> \
  --password <password>

# Create a Kustomization for app based on OCI source
flux create kustomization ghcr-app \
  --source=OCIRepository/ghcr-app \
  --target-namespace=default \
  --namespace=default \
  --prune=true \
  --interval=5m \
  --export > ./apps-infra/ghcr-app/kustomization.yaml

# Check app
kubectl get all
curl localhost:30006
```

##### Separate repo app 4: ghcr-helm-app (imperative way)
##### Using GHCR and Helm chart approach for CD (Auto deploy by scanning GHCR repo for Helm charts)

```
# Pre-Build and push app with Docker (on Win11)
docker build -t olegan/ghcr-helm-app:0.0.1 ./src
docker push olegan/ghcr-helm-app:0.0.1

# Install Helm (if need)
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Creating Helm Repository (based on GitHub pages)
helm package ./helm-chart/

# Loging to GHCR registry with helm 
helm registry login ghcr.io -u olg-man 
OR
docker login ghcr.io -u olg-man 

# Push Helm chart/package to GHCR
helm push ghcr-helm-app-0.0.1.tgz oci://ghcr.io/olg-man/
```

```
# Create an Helm repo based OCI GHCR source
flux create source helm ghcr-helm-app \
  --url=oci://ghcr.io/olg-man \
  --namespace=default \
  --export > ./apps-infra/ghcr-helm-app/ocisource.yaml

# Create a HelmRelease for app based on OCI source
flux create hr ghcr-helm-app \
  --release-name=ghcr-helm-app \
  --target-namespace=default \
  --namespace=default \
  --source=HelmRepository/ghcr-helm-app \
  --chart=ghcr-helm-app \
  --interval=1m \
  --export > ./apps-infra/ghcr-helm-app/helmrelease.yaml

# Optionally, Helm analog of deploy your chart from ghcr
helm upgrade --install ghcr-helm-app oci://ghcr.io/olg-man/ghcr-helm-app --version 0.0.1

# Check app
kubectl get all
curl localhost:30007
```

##### Python k8s info app
```
# Build and push app with Docker (on Win11) 
docker build -t olegan/k8s-info-app:0.0.1 ./apps/base-python-app/src
docker push olegan/k8s-info-app:0.0.1

# Apply on kind cluster
kubectl apply -f ./apps/base-python-app/deploy/  
```
 
##### Monitoring (TBD)
```
# Using https://github.com/fluxcd/flux2-monitoring-example as a base and implement it in our demo
in paths:
./monitoring
./scripting
./flux-cluster/demo-cluster/monitoring.yaml

# Bootstraping flux cluster with monitoring
flux bootstrap github \
  --token-auth \
  --owner=OLG-MAN \
  --repository=gitops_demo \
  --branch=main \
  --path=./flux-clusters/demo-cluster \
  --components-extra=image-reflector-controller,image-automation-controller \
  --personal
```
 
##### Prometheus, Grafana, Loki (TBD)


##### Secrets Management (TBD)
##### Sealed Secrets, SOPS (TBD)


----------------------------------------------------------------------------------------------------------------------------