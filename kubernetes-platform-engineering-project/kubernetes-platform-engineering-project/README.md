# Kubernetes Platform Deployment with CI/CD and GitOps

DevOps project demonstrating how to package, secure, deploy, scale, and continuously deliver a containerized application to Kubernetes.

> **Portfolio note:** This is a hands-on lab project. Deploy it, capture your own evidence, and document the decisions and troubleshooting you perform. Do not claim production use unless it has genuinely been used in production.

## Project architecture

```text
Developer
   |
   | git push
   v
GitHub repository
   |
   v
GitHub Actions CI
   |-- lint / test
   |-- build container image
   |-- scan image with Trivy
   |-- push image to GHCR
   |
   v
GitOps deployment repository (this repository)
   |
   v
Argo CD watches Kubernetes manifests
   |
   v
Kubernetes cluster
   |-- Namespace
   |-- Deployment (2 replicas)
   |-- ClusterIP Service
   |-- Ingress
   |-- ConfigMap
   |-- Secret (example only)
   |-- HPA
   |-- PodDisruptionBudget
   |-- NetworkPolicy
   |-- ServiceAccount
   |
   v
Containerized Flask application
```

## What you will implement

- Containerize a small Python Flask application using a multi-stage Docker build.
- Run the container as a non-root user with a read-only root filesystem.
- Deploy two replicas using Kubernetes Deployments.
- Expose the application internally with a ClusterIP Service and externally through an Ingress controller.
- Separate non-sensitive configuration into a ConfigMap.
- Use a Kubernetes Secret reference for sensitive configuration (demo value only).
- Configure startup, readiness, and liveness probes.
- Set CPU and memory requests/limits.
- Configure Horizontal Pod Autoscaling (HPA).
- Add a PodDisruptionBudget and a basic NetworkPolicy.
- Use GitHub Actions to test, build, scan, and publish an image to GitHub Container Registry (GHCR).
- Use Argo CD to continuously reconcile the Kubernetes manifests from Git.

## Repository layout

```text
kubernetes-platform-engineering-project/
├── app/
│   ├── app.py
│   └── requirements.txt
├── tests/
│   └── test_app.py
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.example.yaml
│   │   ├── serviceaccount.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   ├── hpa.yaml
│   │   ├── pdb.yaml
│   │   ├── networkpolicy.yaml
│   │   └── kustomization.yaml
│   └── argocd/
│       └── application.yaml
├── .github/workflows/
│   └── ci-cd.yaml
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

## Prerequisites

For a Windows 11 workstation:

- Docker Desktop
- kubectl
- A Kubernetes cluster (Docker Desktop Kubernetes, Minikube, or a managed cluster)
- An Ingress controller installed in the cluster (for example, ingress-nginx)
- Metrics Server installed for HPA metrics
- Argo CD installed if you want to complete the GitOps stage
- A GitHub account and a repository

Check your tools and cluster:

```powershell
docker version
kubectl version --client
kubectl get nodes
```

## Stage 1 — Build and test locally

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
pip install pytest
$env:PYTHONPATH = "."
pytest -q
```

Build and run the container:

```powershell
docker build -t platform-demo:local .
docker run --rm -p 8080:8080 platform-demo:local
```

Open `http://localhost:8080/health`.

## Stage 2 — Publish an image to GHCR

1. Create a GitHub repository and push this project.
2. In GitHub, open **Settings → Actions → General** and allow the workflow permissions needed to write packages.
3. The workflow uses the built-in `GITHUB_TOKEN` and publishes to GHCR.
4. Push to the `main` branch. Check the Actions tab for test, build, and image scan results.

The image name is based on the GitHub repository owner and repository name. The workflow writes the published image reference to the GitHub Actions run summary.

For a private GHCR package, configure Kubernetes `imagePullSecrets` before deploying. For a public package, no pull secret is required.

## Stage 3 — Configure the image for Kubernetes

Edit `k8s/base/deployment.yaml` and replace:

```text
ghcr.io/REPLACE_WITH_OWNER/REPLACE_WITH_REPOSITORY:latest
```

with the actual image published by your GitHub Actions workflow, preferably using an immutable version tag or commit SHA rather than `latest`.

## Stage 4 — Deploy to Kubernetes

Make sure an Ingress controller and Metrics Server are installed in your cluster.

Apply the example Secret (demo value only), then deploy the base resources:

```powershell
kubectl apply -f k8s/base/secret.example.yaml
kubectl apply -k k8s/base
```

Check the rollout:

```powershell
kubectl get all -n platform-demo
kubectl get ingress -n platform-demo
kubectl rollout status deployment/platform-demo -n platform-demo
```

For local testing without Ingress DNS configuration, port-forward the Service:

```powershell
kubectl port-forward service/platform-demo 8080:80 -n platform-demo
```

Open `http://localhost:8080/health`.

## Stage 5 — Test scaling and resilience

Check HPA:

```powershell
kubectl get hpa -n platform-demo
kubectl top pods -n platform-demo
```

HPA requires Metrics Server and resource requests. Generate traffic to observe scaling; do not expect scale-out until the CPU target is exceeded and metrics are available.

Check disruption budget and network policy:

```powershell
kubectl get pdb,networkpolicy -n platform-demo
```

## Stage 6 — GitOps with Argo CD

1. Install Argo CD in your cluster using the official Argo CD installation instructions.
2. Replace the `repoURL` in `k8s/argocd/application.yaml` with your Git repository URL.
3. Apply the Argo CD Application:

```powershell
kubectl apply -f k8s/argocd/application.yaml
```

4. Open the Argo CD UI and verify that the application becomes Synced and Healthy.
5. Change a Kubernetes manifest, commit and push it, then observe Argo CD reconcile the cluster.

Do not enable automated pruning or self-healing until you understand the impact of GitOps reconciliation in your cluster.

## Security considerations

- The container runs as a non-root user.
- The root filesystem is read-only; `/tmp` is mounted as writable `emptyDir`.
- Kubernetes resource requests and limits are set.
- A ServiceAccount is explicitly assigned and automatic token mounting is disabled.
- A NetworkPolicy is included as a baseline. It assumes an Ingress controller in the `ingress-nginx` namespace; adjust labels and namespace selectors for your cluster CNI and ingress installation.
- `secret.example.yaml` contains a placeholder demo value only. Do not commit real credentials. For real environments, use an external secret manager such as Azure Key Vault, AWS Secrets Manager, or an External Secrets Operator.
- Trivy scanning in CI is a basic image vulnerability check, not a guarantee of security.
- Review manifests and cloud costs before deploying to a managed cluster.

## Troubleshooting

```powershell
kubectl describe deployment platform-demo -n platform-demo
kubectl describe pods -n platform-demo
kubectl logs deployment/platform-demo -n platform-demo
kubectl get events -n platform-demo --sort-by=.metadata.creationTimestamp
kubectl describe hpa platform-demo -n platform-demo
```

Common causes:
- `ImagePullBackOff`: verify the GHCR image name, tag, and package visibility or pull secret.
- Ingress has no address: check that an Ingress controller is installed and running.
- HPA shows unknown metrics: install or repair Metrics Server and check CPU requests.
- NetworkPolicy blocks traffic: verify your CNI supports NetworkPolicy and adjust the ingress-controller namespace/labels.

## Suggested evidence to add to your portfolio

After you run the project, add your own screenshots under an `images/` folder:

- GitHub Actions successful pipeline
- GHCR published image
- `kubectl get pods,svc,ingress -n platform-demo`
- HPA output while scaling
- Argo CD Synced / Healthy application
- Application `/health` endpoint in the browser

Only include screenshots from your actual deployment.
