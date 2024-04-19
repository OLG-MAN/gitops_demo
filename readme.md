### GitOps DEMO 

Infrastructure - wsl2 + [kind](https://kind.sigs.k8s.io/docs/user/using-wsl2/) cluster
CICD tools     - GitHub Actions, [FluxCD](https://fluxcd.io/flux/get-started/)
OCI            - DockerHub, GitHub Container Registry (GHCR)

#### Demo Steps

##### Install Steps

```
# Test with Nginx

kind create cluster --config=cluster-config.yml
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

curl -s https://fluxcd.io/install.sh | sudo bash

# And make pre=check

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

##### Git Source with Flux (base example)

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
