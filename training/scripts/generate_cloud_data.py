#!/usr/bin/env python3
"""
Cloud & DevOps Training Data Generator
Target: ~250 examples for cloud services, CI/CD, infrastructure as code
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for cloud infrastructure and DevOps.
You help with cloud services, CI/CD pipelines, infrastructure as code, and deployment strategies."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

CLOUD_CLI_TASKS = [
    # Azure CLI
    {
        "instruction": "Login to Azure CLI",
        "command": "az login",
        "explanation": "Opens browser for Azure authentication"
    },
    {
        "instruction": "List Azure subscriptions",
        "command": "az account list --output table",
        "explanation": "Shows all subscriptions for current user"
    },
    {
        "instruction": "Set Azure subscription",
        "command": "az account set --subscription \"my-subscription-name\"",
        "explanation": "Switches active subscription context"
    },
    {
        "instruction": "Create Azure resource group",
        "command": "az group create --name myResourceGroup --location eastus",
        "explanation": "Creates new resource group in East US"
    },
    {
        "instruction": "Deploy ARM template",
        "command": "az deployment group create --resource-group myRG --template-file main.bicep --parameters params.json",
        "explanation": "Deploys Bicep template to resource group"
    },
    {
        "instruction": "List Azure resource groups",
        "command": "az group list --output table",
        "explanation": "Shows all resource groups in subscription"
    },
    {
        "instruction": "Create Azure Storage Account",
        "command": "az storage account create --name mystorageaccount --resource-group myRG --location eastus --sku Standard_LRS",
        "explanation": "Creates storage account with locally redundant storage"
    },
    {
        "instruction": "Create Azure App Service",
        "command": "az webapp create --name mywebapp --resource-group myRG --plan myAppServicePlan --runtime 'NODE:18-lts'",
        "explanation": "Creates web app with Node.js 18 LTS runtime"
    },
    {
        "instruction": "Deploy to Azure App Service",
        "command": "az webapp deployment source config-zip --resource-group myRG --name mywebapp --src ./app.zip",
        "explanation": "Deploys zip package to App Service"
    },
    {
        "instruction": "Create Azure Container Registry",
        "command": "az acr create --resource-group myRG --name myregistry --sku Basic",
        "explanation": "Creates container registry for Docker images"
    },
    {
        "instruction": "Login to Azure Container Registry",
        "command": "az acr login --name myregistry",
        "explanation": "Authenticates Docker to push/pull from ACR"
    },
    {
        "instruction": "Build and push to ACR",
        "command": "az acr build --registry myregistry --image myapp:v1.0 .",
        "explanation": "Builds Docker image in cloud and pushes to ACR"
    },
    {
        "instruction": "Create Azure Function App",
        "command": "az functionapp create --resource-group myRG --consumption-plan-location eastus --runtime python --functions-version 4 --name myfunctionapp --storage-account mystorageaccount",
        "explanation": "Creates serverless Python function app"
    },
    {
        "instruction": "Get Azure web app logs",
        "command": "az webapp log tail --resource-group myRG --name mywebapp",
        "explanation": "Streams live application logs"
    },
    {
        "instruction": "Create Azure SQL Database",
        "command": "az sql db create --resource-group myRG --server myserver --name mydb --service-objective S0",
        "explanation": "Creates Azure SQL Database with S0 tier"
    },
    {
        "instruction": "Create Azure Key Vault",
        "command": "az keyvault create --name mykeyvault --resource-group myRG --location eastus",
        "explanation": "Creates Key Vault for secrets management"
    },
    {
        "instruction": "Set Key Vault secret",
        "command": "az keyvault secret set --vault-name mykeyvault --name mySecret --value 'supersecret'",
        "explanation": "Stores secret in Key Vault"
    },
    {
        "instruction": "Get Key Vault secret",
        "command": "az keyvault secret show --vault-name mykeyvault --name mySecret --query value -o tsv",
        "explanation": "Retrieves secret value from Key Vault"
    },
    # AWS CLI
    {
        "instruction": "Configure AWS CLI",
        "command": "aws configure",
        "explanation": "Interactive setup for AWS credentials and region"
    },
    {
        "instruction": "List AWS S3 buckets",
        "command": "aws s3 ls",
        "explanation": "Lists all S3 buckets in account"
    },
    {
        "instruction": "Create S3 bucket",
        "command": "aws s3 mb s3://my-unique-bucket-name --region us-east-1",
        "explanation": "Creates new S3 bucket"
    },
    {
        "instruction": "List EC2 instances",
        "command": "aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' --output table",
        "explanation": "Shows instances with name and state"
    },
    {
        "instruction": "Copy file to S3",
        "command": "aws s3 cp myfile.txt s3://mybucket/path/myfile.txt",
        "explanation": "Uploads single file to S3"
    },
    {
        "instruction": "Sync folder to S3",
        "command": "aws s3 sync ./build s3://mybucket/static --delete",
        "explanation": "Syncs local folder to S3, deleting removed files"
    },
    {
        "instruction": "Start EC2 instance",
        "command": "aws ec2 start-instances --instance-ids i-1234567890abcdef0",
        "explanation": "Starts stopped EC2 instance"
    },
    {
        "instruction": "Stop EC2 instance",
        "command": "aws ec2 stop-instances --instance-ids i-1234567890abcdef0",
        "explanation": "Stops running EC2 instance"
    },
    {
        "instruction": "Create AWS Lambda function",
        "command": "aws lambda create-function --function-name myfunction --runtime python3.9 --role arn:aws:iam::123456789:role/lambda-role --handler lambda_function.handler --zip-file fileb://function.zip",
        "explanation": "Creates Lambda function from zip deployment package"
    },
    {
        "instruction": "Invoke AWS Lambda function",
        "command": "aws lambda invoke --function-name myfunction --payload '{\"key\": \"value\"}' output.json",
        "explanation": "Executes Lambda function with payload"
    },
    {
        "instruction": "Get Lambda function logs",
        "command": "aws logs tail /aws/lambda/myfunction --follow",
        "explanation": "Streams CloudWatch logs for Lambda"
    },
    {
        "instruction": "Create RDS database instance",
        "command": "aws rds create-db-instance --db-instance-identifier mydb --db-instance-class db.t3.micro --engine postgres --master-username admin --master-user-password mypassword --allocated-storage 20",
        "explanation": "Creates PostgreSQL RDS instance"
    },
    {
        "instruction": "Create SNS topic",
        "command": "aws sns create-topic --name mynotifications",
        "explanation": "Creates SNS topic for pub/sub messaging"
    },
    {
        "instruction": "Create SQS queue",
        "command": "aws sqs create-queue --queue-name myqueue",
        "explanation": "Creates SQS queue for message queueing"
    },
    {
        "instruction": "Get AWS caller identity",
        "command": "aws sts get-caller-identity",
        "explanation": "Shows current AWS account and IAM identity"
    },
    {
        "instruction": "Assume AWS IAM role",
        "command": "aws sts assume-role --role-arn arn:aws:iam::123456789:role/MyRole --role-session-name mysession",
        "explanation": "Gets temporary credentials for IAM role"
    },
    {
        "instruction": "Create ECR repository",
        "command": "aws ecr create-repository --repository-name myapp",
        "explanation": "Creates Elastic Container Registry repository"
    },
    {
        "instruction": "Login to ECR",
        "command": "aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com",
        "explanation": "Authenticates Docker to AWS ECR"
    },
    {
        "instruction": "Create ECS cluster",
        "command": "aws ecs create-cluster --cluster-name mycluster",
        "explanation": "Creates ECS container cluster"
    },
    # GCP CLI (gcloud)
    {
        "instruction": "Initialize GCP CLI",
        "command": "gcloud init",
        "explanation": "Interactive setup for GCP configuration"
    },
    {
        "instruction": "List GCP projects",
        "command": "gcloud projects list",
        "explanation": "Shows all accessible GCP projects"
    },
    {
        "instruction": "Set GCP project",
        "command": "gcloud config set project my-project-id",
        "explanation": "Switches active GCP project"
    },
    {
        "instruction": "Create GCE instance",
        "command": "gcloud compute instances create myvm --zone us-central1-a --machine-type e2-medium",
        "explanation": "Creates Compute Engine virtual machine"
    },
    {
        "instruction": "SSH to GCE instance",
        "command": "gcloud compute ssh myvm --zone us-central1-a",
        "explanation": "SSHs to instance using IAP or OS Login"
    },
    {
        "instruction": "Create GCS bucket",
        "command": "gsutil mb gs://my-unique-bucket-name",
        "explanation": "Creates Google Cloud Storage bucket"
    },
    {
        "instruction": "Deploy to Cloud Run",
        "command": "gcloud run deploy myservice --image gcr.io/myproject/myapp --platform managed --region us-central1 --allow-unauthenticated",
        "explanation": "Deploys container to serverless Cloud Run"
    },
    {
        "instruction": "Deploy Cloud Function",
        "command": "gcloud functions deploy myfunction --runtime python39 --trigger-http --allow-unauthenticated",
        "explanation": "Deploys HTTP-triggered Cloud Function"
    },
    {
        "instruction": "Create GKE cluster",
        "command": "gcloud container clusters create mycluster --zone us-central1-a --num-nodes 3",
        "explanation": "Creates Google Kubernetes Engine cluster"
    },
    {
        "instruction": "Get GKE credentials",
        "command": "gcloud container clusters get-credentials mycluster --zone us-central1-a",
        "explanation": "Configures kubectl for GKE cluster access"
    },
]

KUBERNETES_TASKS = [
    {
        "instruction": "Get Kubernetes cluster info",
        "command": "kubectl cluster-info",
        "explanation": "Shows master and services URLs"
    },
    {
        "instruction": "List pods in all namespaces",
        "command": "kubectl get pods -A",
        "explanation": "Shows all pods across namespaces"
    },
    {
        "instruction": "Describe a pod for debugging",
        "command": "kubectl describe pod <pod-name> -n <namespace>",
        "explanation": "Shows events and details for troubleshooting"
    },
    {
        "instruction": "View pod logs",
        "command": "kubectl logs <pod-name> -n <namespace> --tail=100 -f",
        "explanation": "Follows last 100 lines of pod logs"
    },
    {
        "instruction": "Apply Kubernetes manifest",
        "command": "kubectl apply -f deployment.yaml",
        "explanation": "Creates or updates resources from file"
    },
    {
        "instruction": "Scale deployment",
        "command": "kubectl scale deployment myapp --replicas=5",
        "explanation": "Scales to 5 replicas"
    },
    {
        "instruction": "Get deployment rollout status",
        "command": "kubectl rollout status deployment/myapp",
        "explanation": "Watches deployment progress"
    },
    {
        "instruction": "Rollback deployment",
        "command": "kubectl rollout undo deployment/myapp",
        "explanation": "Reverts to previous deployment version"
    },
    {
        "instruction": "Port forward to pod",
        "command": "kubectl port-forward pod/myapp-xxx 8080:80",
        "explanation": "Forwards local port 8080 to pod port 80"
    },
    {
        "instruction": "Execute command in pod",
        "command": "kubectl exec -it <pod-name> -n <namespace> -- /bin/bash",
        "explanation": "Opens interactive shell in container"
    },
    {
        "instruction": "Get all Kubernetes resources",
        "command": "kubectl get all -n <namespace>",
        "explanation": "Lists deployments, services, pods, replicasets"
    },
    {
        "instruction": "Get Kubernetes nodes",
        "command": "kubectl get nodes -o wide",
        "explanation": "Shows node status, IPs, and versions"
    },
    {
        "instruction": "Get node resource usage",
        "command": "kubectl top nodes",
        "explanation": "Shows CPU and memory usage per node"
    },
    {
        "instruction": "Get pod resource usage",
        "command": "kubectl top pods -n <namespace>",
        "explanation": "Shows CPU and memory per pod"
    },
    {
        "instruction": "Create namespace",
        "command": "kubectl create namespace production",
        "explanation": "Creates new namespace for isolation"
    },
    {
        "instruction": "Delete pod",
        "command": "kubectl delete pod <pod-name> -n <namespace>",
        "explanation": "Deletes pod (deployment will recreate it)"
    },
    {
        "instruction": "Force delete stuck pod",
        "command": "kubectl delete pod <pod-name> --grace-period=0 --force",
        "explanation": "Forcefully removes stuck terminating pod"
    },
    {
        "instruction": "Get services",
        "command": "kubectl get svc -n <namespace>",
        "explanation": "Lists services with cluster IPs and ports"
    },
    {
        "instruction": "Get ingresses",
        "command": "kubectl get ingress -A",
        "explanation": "Lists all ingress resources across namespaces"
    },
    {
        "instruction": "Get secrets",
        "command": "kubectl get secrets -n <namespace>",
        "explanation": "Lists secrets in namespace"
    },
    {
        "instruction": "Create secret from literal",
        "command": "kubectl create secret generic my-secret --from-literal=username=admin --from-literal=password=secret123",
        "explanation": "Creates secret with key-value pairs"
    },
    {
        "instruction": "Create secret from file",
        "command": "kubectl create secret generic tls-cert --from-file=cert.pem --from-file=key.pem",
        "explanation": "Creates secret from certificate files"
    },
    {
        "instruction": "Decode secret value",
        "command": "kubectl get secret my-secret -o jsonpath='{.data.password}' | base64 -d",
        "explanation": "Extracts and decodes secret value"
    },
    {
        "instruction": "Create configmap from file",
        "command": "kubectl create configmap app-config --from-file=config.yaml",
        "explanation": "Creates ConfigMap from configuration file"
    },
    {
        "instruction": "Get configmap data",
        "command": "kubectl get configmap app-config -o yaml",
        "explanation": "Shows ConfigMap contents"
    },
    {
        "instruction": "Edit resource in place",
        "command": "kubectl edit deployment myapp",
        "explanation": "Opens deployment in editor for live changes"
    },
    {
        "instruction": "Set deployment image",
        "command": "kubectl set image deployment/myapp myapp=myregistry/myapp:v2.0",
        "explanation": "Updates container image for rolling update"
    },
    {
        "instruction": "Get rollout history",
        "command": "kubectl rollout history deployment/myapp",
        "explanation": "Shows deployment revision history"
    },
    {
        "instruction": "Rollback to specific revision",
        "command": "kubectl rollout undo deployment/myapp --to-revision=2",
        "explanation": "Reverts to specific revision number"
    },
    {
        "instruction": "Create horizontal pod autoscaler",
        "command": "kubectl autoscale deployment myapp --min=2 --max=10 --cpu-percent=80",
        "explanation": "Enables autoscaling based on CPU usage"
    },
    {
        "instruction": "Get HPA status",
        "command": "kubectl get hpa",
        "explanation": "Shows autoscaler current and target metrics"
    },
    {
        "instruction": "Get events for debugging",
        "command": "kubectl get events -n <namespace> --sort-by='.lastTimestamp'",
        "explanation": "Shows recent events sorted by time"
    },
    {
        "instruction": "Drain node for maintenance",
        "command": "kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data",
        "explanation": "Evicts pods before node maintenance"
    },
    {
        "instruction": "Cordon node",
        "command": "kubectl cordon <node-name>",
        "explanation": "Marks node unschedulable for new pods"
    },
    {
        "instruction": "Uncordon node",
        "command": "kubectl uncordon <node-name>",
        "explanation": "Returns node to schedulable state"
    },
    {
        "instruction": "Apply kustomization",
        "command": "kubectl apply -k ./overlays/production",
        "explanation": "Applies Kustomize overlay configuration"
    },
    {
        "instruction": "Dry run apply",
        "command": "kubectl apply -f deployment.yaml --dry-run=client -o yaml",
        "explanation": "Shows what would be applied without doing it"
    },
    {
        "instruction": "Get pod by label",
        "command": "kubectl get pods -l app=myapp,environment=production",
        "explanation": "Filters pods by label selectors"
    },
    {
        "instruction": "Watch resource changes",
        "command": "kubectl get pods -w",
        "explanation": "Watches for pod status changes in real-time"
    },
    {
        "instruction": "Copy file from pod",
        "command": "kubectl cp <namespace>/<pod-name>:/path/to/file ./local-file",
        "explanation": "Copies file from pod to local machine"
    },
    {
        "instruction": "Copy file to pod",
        "command": "kubectl cp ./local-file <namespace>/<pod-name>:/path/to/destination",
        "explanation": "Copies local file into pod container"
    },
    {
        "instruction": "Get pod YAML definition",
        "command": "kubectl get pod <pod-name> -o yaml > pod-backup.yaml",
        "explanation": "Exports pod definition to YAML file"
    },
    {
        "instruction": "Debug with temporary container",
        "command": "kubectl debug -it <pod-name> --image=busybox --target=<container-name>",
        "explanation": "Attaches debug container to running pod"
    },
    {
        "instruction": "Run one-off pod",
        "command": "kubectl run debug-pod --rm -it --image=alpine -- /bin/sh",
        "explanation": "Runs temporary pod for debugging"
    },
    {
        "instruction": "Get persistent volumes",
        "command": "kubectl get pv",
        "explanation": "Lists cluster-wide persistent volumes"
    },
    {
        "instruction": "Get persistent volume claims",
        "command": "kubectl get pvc -n <namespace>",
        "explanation": "Lists PVCs in namespace"
    },
    {
        "instruction": "Get storage classes",
        "command": "kubectl get storageclass",
        "explanation": "Shows available storage classes"
    },
    {
        "instruction": "Apply manifest from URL",
        "command": "kubectl apply -f https://raw.githubusercontent.com/user/repo/main/manifest.yaml",
        "explanation": "Applies manifest directly from GitHub"
    },
    {
        "instruction": "Get API resources",
        "command": "kubectl api-resources",
        "explanation": "Lists all available Kubernetes resource types"
    },
    {
        "instruction": "Explain resource fields",
        "command": "kubectl explain deployment.spec.strategy",
        "explanation": "Shows documentation for resource fields"
    },
    {
        "instruction": "Get current context",
        "command": "kubectl config current-context",
        "explanation": "Shows active cluster/user context"
    },
    {
        "instruction": "Switch context",
        "command": "kubectl config use-context my-cluster",
        "explanation": "Switches to different cluster context"
    },
    {
        "instruction": "List contexts",
        "command": "kubectl config get-contexts",
        "explanation": "Shows all configured cluster contexts"
    },
]

TERRAFORM_TASKS = [
    {
        "instruction": "Initialize Terraform workspace",
        "command": "terraform init",
        "explanation": "Downloads providers and initializes backend"
    },
    {
        "instruction": "Format Terraform files",
        "command": "terraform fmt -recursive",
        "explanation": "Formats all .tf files recursively"
    },
    {
        "instruction": "Validate Terraform configuration",
        "command": "terraform validate",
        "explanation": "Checks configuration syntax"
    },
    {
        "instruction": "Plan Terraform changes",
        "command": "terraform plan -out=tfplan",
        "explanation": "Shows planned changes, saves plan file"
    },
    {
        "instruction": "Apply Terraform plan",
        "command": "terraform apply tfplan",
        "explanation": "Applies saved plan"
    },
    {
        "instruction": "Destroy Terraform resources",
        "command": "terraform destroy -auto-approve",
        "explanation": "Destroys all managed resources"
    },
    {
        "instruction": "Show Terraform state",
        "command": "terraform state list",
        "explanation": "Lists all resources in state"
    },
    {
        "instruction": "Import existing resource to Terraform",
        "command": "terraform import aws_instance.example i-1234567890abcdef0",
        "explanation": "Imports existing AWS instance into state"
    },
    {
        "instruction": "Show specific resource in state",
        "command": "terraform state show aws_instance.example",
        "explanation": "Displays attributes of resource in state"
    },
    {
        "instruction": "Remove resource from state",
        "command": "terraform state rm aws_instance.example",
        "explanation": "Removes resource from state without destroying"
    },
    {
        "instruction": "Move resource in state",
        "command": "terraform state mv aws_instance.old aws_instance.new",
        "explanation": "Renames resource in state file"
    },
    {
        "instruction": "Refresh Terraform state",
        "command": "terraform refresh",
        "explanation": "Updates state with real infrastructure"
    },
    {
        "instruction": "Output Terraform values",
        "command": "terraform output -json",
        "explanation": "Shows all outputs in JSON format"
    },
    {
        "instruction": "Get specific output value",
        "command": "terraform output -raw database_url",
        "explanation": "Gets raw output value for scripting"
    },
    {
        "instruction": "Plan with variable file",
        "command": "terraform plan -var-file=prod.tfvars",
        "explanation": "Uses specific variable file"
    },
    {
        "instruction": "Plan with inline variable",
        "command": "terraform plan -var='instance_count=5'",
        "explanation": "Overrides variable on command line"
    },
    {
        "instruction": "Target specific resource",
        "command": "terraform apply -target=aws_instance.web",
        "explanation": "Applies changes only to targeted resource"
    },
    {
        "instruction": "Generate Terraform graph",
        "command": "terraform graph | dot -Tpng > graph.png",
        "explanation": "Creates visual dependency graph"
    },
    {
        "instruction": "Taint resource for recreation",
        "command": "terraform taint aws_instance.example",
        "explanation": "Marks resource for destruction and recreation"
    },
    {
        "instruction": "Untaint resource",
        "command": "terraform untaint aws_instance.example",
        "explanation": "Removes taint from resource"
    },
    {
        "instruction": "Initialize with backend config",
        "command": "terraform init -backend-config=backend.hcl",
        "explanation": "Initializes with separate backend configuration"
    },
    {
        "instruction": "Migrate state to new backend",
        "command": "terraform init -migrate-state",
        "explanation": "Migrates existing state to new backend"
    },
    {
        "instruction": "Reconfigure backend",
        "command": "terraform init -reconfigure",
        "explanation": "Reconfigures backend without state migration"
    },
    {
        "instruction": "Upgrade providers",
        "command": "terraform init -upgrade",
        "explanation": "Upgrades providers to latest versions"
    },
    {
        "instruction": "Lock provider versions",
        "command": "terraform providers lock -platform=linux_amd64 -platform=darwin_amd64",
        "explanation": "Creates dependency lock file for platforms"
    },
    {
        "instruction": "Show provider versions",
        "command": "terraform providers",
        "explanation": "Lists providers required by configuration"
    },
    {
        "instruction": "Create workspace",
        "command": "terraform workspace new staging",
        "explanation": "Creates new Terraform workspace"
    },
    {
        "instruction": "List workspaces",
        "command": "terraform workspace list",
        "explanation": "Shows all available workspaces"
    },
    {
        "instruction": "Select workspace",
        "command": "terraform workspace select production",
        "explanation": "Switches to different workspace"
    },
    {
        "instruction": "Show current workspace",
        "command": "terraform workspace show",
        "explanation": "Displays currently selected workspace"
    },
    {
        "instruction": "Force unlock state",
        "command": "terraform force-unlock <lock-id>",
        "explanation": "Forcibly removes state lock (use with caution)"
    },
    {
        "instruction": "Console interactive mode",
        "command": "terraform console",
        "explanation": "Opens REPL for testing expressions"
    },
    {
        "instruction": "Show Terraform version",
        "command": "terraform version",
        "explanation": "Displays Terraform and provider versions"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up GitHub Actions CI/CD pipeline for Node.js app",
        "steps": [
            "Create .github/workflows directory",
            "Create ci.yml workflow file",
            "Define trigger events (push, pull_request)",
            "Set up job with ubuntu-latest runner",
            "Checkout code with actions/checkout@v4",
            "Setup Node.js with actions/setup-node@v4",
            "Cache node_modules with actions/cache@v3",
            "Run npm ci for clean install",
            "Run linting (npm run lint)",
            "Run tests (npm test)",
            "Build application (npm run build)",
            "Add deployment job with environment protection",
            "Configure secrets for deployment credentials",
            "Add status badges to README"
        ]
    },
    {
        "instruction": "Deploy containerized app to Kubernetes",
        "steps": [
            "Build Docker image with version tag",
            "Push image to container registry (ACR/ECR/GCR)",
            "Create Kubernetes namespace for app",
            "Create ConfigMap for environment variables",
            "Create Secret for sensitive data",
            "Write Deployment manifest with resource limits",
            "Add readiness and liveness probes",
            "Create Service for internal networking",
            "Create Ingress for external access",
            "Configure Horizontal Pod Autoscaler",
            "Apply manifests with kubectl",
            "Verify rollout status",
            "Test health endpoints",
            "Set up monitoring with Prometheus/Grafana"
        ]
    },
    {
        "instruction": "Set up Azure AKS cluster with Terraform",
        "steps": [
            "Create Terraform providers.tf with azurerm provider",
            "Define variables for cluster configuration",
            "Create resource group",
            "Create virtual network and subnet",
            "Create AKS cluster resource",
            "Configure node pools with autoscaling",
            "Enable Azure AD integration for RBAC",
            "Configure Azure Monitor for containers",
            "Create Azure Container Registry",
            "Grant AKS pull access to ACR",
            "Run terraform init",
            "Run terraform plan and review",
            "Run terraform apply",
            "Get kubeconfig: az aks get-credentials",
            "Verify cluster access"
        ]
    },
    {
        "instruction": "Implement blue-green deployment",
        "steps": [
            "Ensure current production (blue) is stable",
            "Deploy new version to green environment",
            "Run smoke tests on green",
            "Run integration tests on green",
            "Verify green health checks pass",
            "Update load balancer/router to point to green",
            "Monitor error rates and latency",
            "If issues: immediately switch back to blue",
            "If stable: mark green as new blue",
            "Keep old blue running for quick rollback",
            "After validation period: decommission old blue",
            "Document deployment in changelog"
        ]
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Write Kubernetes deployment manifest",
        "language": "yaml",
        "code": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myregistry.azurecr.io/myapp:v1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP""",
        "explanation": "Complete deployment with health checks, resource limits, and service"
    },
    {
        "instruction": "Write GitHub Actions workflow for Docker build and push",
        "language": "yaml",
        "code": """name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=sha,prefix=

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max""",
        "explanation": "Multi-arch Docker build with caching and semantic versioning"
    },
    {
        "instruction": "Write Terraform Azure AKS cluster",
        "language": "hcl",
        "code": """terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "aks" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
    enable_auto_scaling = true
    min_count           = var.min_count
    max_count           = var.max_count
    vnet_subnet_id      = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.aks.id
  }

  tags = var.tags
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}""",
        "explanation": "AKS cluster with autoscaling, monitoring, and managed identity"
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is Infrastructure as Code (IaC)?",
        "answer": "IaC manages infrastructure through code rather than manual processes. Benefits: version control, repeatability, consistency, documentation. Tools: Terraform (multi-cloud), Bicep/ARM (Azure), CloudFormation (AWS), Pulumi (programming languages). Workflow: write config → plan → apply → state managed. Enables GitOps, code review for infra changes, disaster recovery. State files track resource mappings. Idempotent - running same code yields same result."
    },
    {
        "question": "What is a CI/CD pipeline?",
        "answer": "CI/CD automates software delivery. Continuous Integration: automatically build and test on every commit, catch issues early. Continuous Deployment: automatically deploy passing builds to production. Pipeline stages: source → build → test → deploy. Tools: GitHub Actions, Azure DevOps, Jenkins, GitLab CI. Key practices: fast feedback, automated testing, infrastructure as code, feature flags. CD can mean Delivery (manual approval) or Deployment (fully automated)."
    },
    {
        "question": "What is Kubernetes?",
        "answer": "Kubernetes (K8s) orchestrates containerized applications across clusters. Core concepts: Pods (containers), Deployments (desired state), Services (networking), Ingress (external access). Control plane schedules pods to worker nodes. Self-healing: restarts failed containers, scales based on load. Declarative: describe desired state, K8s makes it happen. Ecosystem: Helm (packages), operators (custom controllers), service mesh (Istio). Major clouds offer managed K8s: AKS, EKS, GKE."
    },
    {
        "question": "What are container registries?",
        "answer": "Container registries store and distribute Docker images. Types: public (Docker Hub, GitHub Packages) and private (ACR, ECR, GCR). Features: vulnerability scanning, access control, geo-replication. Image naming: registry/repository:tag (e.g., ghcr.io/user/app:v1.0). Use tags for versioning, immutable tags for production. Pull secrets authenticate K8s to private registries. Registry mirror/cache reduces external pulls. Clean up old images to save storage."
    },
    {
        "question": "What is Docker and why use containers?",
        "answer": "Docker packages applications with dependencies into containers. Benefits: consistent environments (works on my machine → works everywhere), isolation, fast startup, efficient resource usage. Dockerfile defines image build steps. docker-compose orchestrates multi-container apps locally. Containers vs VMs: containers share host OS kernel, lighter weight. Image layers are cached for faster builds. Use multi-stage builds to reduce final image size. Best practice: one process per container, non-root user, minimal base images (alpine)."
    },
    {
        "question": "What is a load balancer?",
        "answer": "Load balancers distribute traffic across multiple servers. Types: Layer 4 (TCP/UDP, faster) vs Layer 7 (HTTP, content-aware routing). Algorithms: round-robin, least connections, IP hash, weighted. Health checks remove unhealthy targets. Cloud offerings: Azure Load Balancer/App Gateway, AWS ALB/NLB/ELB, GCP Load Balancing. K8s Services provide internal load balancing, Ingress for external. Use for high availability, scalability, SSL termination. Consider sticky sessions for stateful apps."
    },
    {
        "question": "What are environment variables and secrets?",
        "answer": "Environment variables configure applications without code changes. Use for: database URLs, API endpoints, feature flags. Secrets are sensitive env vars: API keys, passwords, connection strings. Never commit secrets to Git! Solutions: .env files (local), GitHub Actions secrets, Azure Key Vault, AWS Secrets Manager. K8s ConfigMaps (non-sensitive) vs Secrets (base64, not encrypted). 12-factor app: store config in environment. Access in code: process.env.VAR_NAME (Node), os.environ['VAR'] (Python)."
    },
    {
        "question": "What is DNS and how does it work?",
        "answer": "DNS translates domain names to IP addresses. Record types: A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), TXT (verification), NS (nameservers). TTL controls caching duration. Resolution: browser cache → OS cache → resolver → root → TLD → authoritative. Cloud DNS: Azure DNS, Route 53, Cloud DNS. Use low TTL before migrations, higher for production. Private DNS zones for internal resolution. DNSSEC adds security against spoofing."
    },
    {
        "question": "What is a VPN and VNet/VPC?",
        "answer": "VNet (Azure) / VPC (AWS/GCP) is a private network in the cloud. Isolates resources, controls traffic with NSGs/Security Groups. Subnets divide VNet by purpose (web, app, db). VPN connects on-premises to cloud securely. Site-to-site VPN: always-on connection. Point-to-site: individual clients. ExpressRoute/Direct Connect: dedicated private connection (not over internet). Peering connects VNets together. Use private endpoints to access PaaS services without public internet."
    },
    {
        "question": "What is a CDN (Content Delivery Network)?",
        "answer": "CDN caches content at edge locations close to users. Benefits: reduced latency, lower origin load, DDoS protection. Cache: static assets (images, CSS, JS), API responses. Cloud CDNs: Azure CDN, CloudFront, Cloud CDN. Configuration: cache rules, TTL, purge/invalidation. Origin: your server or storage (S3, Blob). Use cache-busting (version in filename) for updates. Consider: dynamic site acceleration, image optimization, WAF integration. Monitor cache hit ratio."
    },
    {
        "question": "What is serverless computing?",
        "answer": "Serverless runs code without managing servers. Pay per execution, auto-scales to zero. Services: Azure Functions, AWS Lambda, Cloud Functions. Triggers: HTTP, queue, timer, events. Cold start: first invocation slower (keep warm or use provisioned concurrency). Best for: event-driven, sporadic workloads, APIs. Limitations: execution time limits, stateless, vendor lock-in. Serverless databases: Cosmos DB serverless, DynamoDB on-demand, Aurora Serverless. Consider FaaS vs containers based on workload patterns."
    },
    {
        "question": "What is blob/object storage?",
        "answer": "Object storage stores unstructured data as objects with metadata. Services: Azure Blob, S3, Cloud Storage. Tiers: hot (frequent access), cool (infrequent), archive (rarely accessed). Use cases: backups, static websites, data lakes, media. Access: URLs, SDKs, mounted as filesystem. Security: private by default, SAS tokens, IAM policies. Lifecycle policies auto-move to cheaper tiers. Enable versioning for recovery. Cross-region replication for DR. Cost: storage + operations + egress."
    },
    {
        "question": "What are managed databases in the cloud?",
        "answer": "Managed databases handle backups, patching, HA automatically. Relational: Azure SQL, RDS, Cloud SQL. NoSQL: Cosmos DB, DynamoDB, Firestore. Options: single server, read replicas, multi-region. Choose based on: consistency needs, query patterns, scale requirements. Connection pooling prevents exhausting connections. Use connection strings from secrets/env vars. Monitor: DTU/vCore usage, storage, slow queries. Consider serverless tier for variable workloads. Private endpoints for security."
    },
    {
        "question": "What is a service mesh?",
        "answer": "Service mesh manages service-to-service communication in microservices. Sidecar proxy pattern: Envoy injected alongside each service. Features: mTLS (encryption), traffic management, observability, retries. Implementations: Istio, Linkerd, Consul Connect. K8s native mesh options emerging. Use cases: zero-trust networking, canary deployments, distributed tracing. Adds complexity - evaluate if needed. Start with basic K8s Services, add mesh when complexity grows. Alternative: library-based approach (no sidecar overhead)."
    },
    {
        "question": "What is auto-scaling?",
        "answer": "Auto-scaling adjusts resources based on demand. Horizontal: add/remove instances. Vertical: resize instances (usually requires restart). K8s: HPA (pods), VPA (resources), Cluster Autoscaler (nodes). Cloud: VM Scale Sets, Auto Scaling Groups. Metrics: CPU, memory, queue length, custom metrics. Scale-out fast, scale-in slow (avoid thrashing). Minimum instances for availability. Consider: startup time, warm-up period, cost implications. Predictive scaling for known patterns. Test scale behavior under load."
    },
    {
        "question": "What is a reverse proxy?",
        "answer": "Reverse proxy sits in front of servers, handling client requests. Uses: SSL termination, load balancing, caching, compression, security. Tools: Nginx, HAProxy, Traefik, Envoy. K8s Ingress controllers are reverse proxies. Configuration: upstream servers, routing rules, timeouts. Security: hide backend details, rate limiting, request filtering. Headers: X-Forwarded-For (real client IP), X-Real-IP. WebSocket support for real-time apps. Health checks for backend availability."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What is GitOps?",
        "answer": "GitOps uses Git as single source of truth for infrastructure and applications. Core principles: declarative config in Git, automated sync to cluster, drift detection and reconciliation. Tools: ArgoCD, Flux. Workflow: PR review → merge to main → operator syncs cluster. Benefits: audit trail, easy rollback (git revert), consistent environments. Challenges: secrets management (use sealed secrets, external secrets), handling stateful apps. Not just 'git push to deploy' - includes continuous reconciliation."
    },
    {
        "question": "How do you implement zero-downtime deployments?",
        "answer": "Strategies: rolling update (replace pods gradually), blue-green (switch traffic instantly), canary (gradual traffic shift). K8s rolling update: maxSurge, maxUnavailable settings. Requirements: readiness probes (don't send traffic until ready), graceful shutdown (handle SIGTERM), connection draining. Database migrations: backward compatible schemas, separate deploy from migrate. Use PodDisruptionBudgets for maintenance. Feature flags decouple deploy from release. Monitor error rates during rollout, automated rollback on failures."
    },
    {
        "question": "How do you manage secrets in cloud deployments?",
        "answer": "Never commit secrets to Git. Solutions: Azure Key Vault, AWS Secrets Manager, HashiCorp Vault. K8s secrets: base64 encoded, not encrypted - use external secrets operator or sealed secrets. CI/CD: use platform secrets (GitHub Actions secrets), inject at runtime. Rotation: automate, plan for zero-downtime rotation. Access: least privilege, audit logging. Development: use .env files (in .gitignore), different secrets per environment. Consider: secret scanning in repos, pre-commit hooks."
    },
    {
        "question": "What is observability and the three pillars?",
        "answer": "Observability: ability to understand system state from external outputs. Three pillars: Logs (discrete events, structured JSON, centralized with ELK/Loki), Metrics (time-series data, Prometheus/Grafana, alerting), Traces (request flow across services, Jaeger/Zipkin, spans). Correlation: connect traces to logs with trace IDs. Implement: structured logging, meaningful metrics (RED: Rate, Errors, Duration), distributed tracing. SLOs/SLIs define acceptable performance. Alert on symptoms not causes. Dashboards for different audiences (ops, business)."
    },
    {
        "question": "What is chaos engineering?",
        "answer": "Chaos engineering tests system resilience by intentionally injecting failures. Principles: start small, define steady state, hypothesize, run experiments. Tools: Chaos Monkey (random instance termination), Gremlin, LitmusChaos (K8s). Experiments: kill pods, network latency, disk full, CPU stress, zone failure. Run in production (carefully!) to find real weaknesses. Game days: scheduled chaos exercises. Prerequisites: observability, runbooks, on-call. Build confidence through controlled failure injection."
    },
    {
        "question": "How do you design for high availability?",
        "answer": "HA eliminates single points of failure. Strategies: redundancy (multiple instances), geographic distribution (multi-region), automated failover. Cloud patterns: Availability Zones (separate data centers), paired regions. Database: read replicas, active-active, failover groups. K8s: pod anti-affinity, PodDisruptionBudgets. Load balancer health checks remove failed nodes. Active-passive vs active-active. RTO (recovery time) vs RPO (data loss tolerance). Test failover regularly. Cost consideration: HA isn't free."
    },
    {
        "question": "What is multi-tenancy in cloud architecture?",
        "answer": "Multi-tenancy serves multiple customers (tenants) from shared infrastructure. Models: shared database (row-level isolation), database per tenant, infrastructure per tenant. Considerations: data isolation, noisy neighbor, customization, compliance. K8s approaches: namespace per tenant, cluster per tenant. Database strategies: tenant_id column, schema per tenant, connection pooling. Billing: track resource usage per tenant. Security: never leak data between tenants. Scaling: plan for tenant growth variability."
    },
    {
        "question": "How do you implement disaster recovery?",
        "answer": "DR ensures business continuity after catastrophic failures. Key metrics: RTO (how fast), RPO (how much data loss). Strategies: backup/restore, pilot light, warm standby, hot standby (multi-region active). Components: infrastructure as code, automated deployment, data replication. Test regularly with DR drills. Cloud tools: Azure Site Recovery, AWS Backup, cross-region replication. Runbooks document procedures. Consider: data sovereignty, compliance requirements. Priority: identify critical systems, acceptable downtime per tier."
    },
    {
        "question": "What is infrastructure drift and how do you prevent it?",
        "answer": "Drift: actual infrastructure differs from defined state. Causes: manual changes, failed applies, external modifications. Detection: terraform plan shows pending changes, cloud-specific tools (AWS Config, Azure Policy). Prevention: prohibit manual changes (RBAC), run IaC in CI/CD, regular drift detection scans. Remediation: import changes or revert to defined state. GitOps automatically reconciles drift. Consider: immutable infrastructure (replace, don't modify), policy enforcement. Document exceptions when manual changes necessary."
    },
    {
        "question": "How do you optimize cloud costs?",
        "answer": "Cost optimization pillars: right-sizing, reserved capacity, spot instances, cleanup. Right-size: monitor actual usage, use smaller instance types. Reserved Instances/Savings Plans: 1-3 year commitments for 30-70% savings. Spot instances: 90% savings for fault-tolerant workloads. Cleanup: delete unused resources, stop dev/test after hours. Tools: Azure Cost Management, AWS Cost Explorer, Kubecost (K8s). Tags for allocation. Storage tiers for old data. Set budgets and alerts. FinOps: culture of cost awareness."
    },
    {
        "question": "What is a container orchestration platform comparison (K8s vs alternatives)?",
        "answer": "Kubernetes: industry standard, complex, highly configurable. Managed K8s: AKS, EKS, GKE reduce operational burden. Alternatives: Docker Swarm (simpler, built-in), Nomad (HashiCorp, flexible scheduler), ECS/Fargate (AWS native). Serverless containers: Azure Container Apps, Cloud Run, App Runner. Consider: team expertise, workload complexity, cloud provider. K8s overkill for simple apps. Nomad for mixed workloads (containers + VMs). ECS if AWS-only. Start simple, migrate to K8s when needed."
    },
    {
        "question": "How do you secure container images?",
        "answer": "Image security lifecycle: build → scan → deploy → runtime. Build: minimal base images (distroless, alpine), non-root user, no secrets in image. Scan: Trivy, Snyk, ACR/ECR built-in scanning, fail CI on critical CVEs. Deploy: image signing (Cosign, Notary), admission controllers verify signatures. Runtime: read-only filesystem, drop capabilities, seccomp profiles. Keep base images updated. Scan both during build and continuously (new CVEs discovered). SBOMs document components."
    },
    {
        "question": "What is policy as code?",
        "answer": "Policy as code defines and enforces rules through code. Tools: OPA/Gatekeeper (K8s), Azure Policy, AWS Config Rules, Sentinel (Terraform). Use cases: require labels, enforce resource limits, deny privileged containers, mandate encryption. Workflow: define policy → test → deploy → enforce. Modes: audit (warn) or deny (block). Examples: all S3 buckets encrypted, no public IPs, naming conventions. Benefits: consistent enforcement, audit trail, PR review for policy changes. Start with audit mode, graduate to enforcement."
    },
    {
        "question": "How do you implement blue-green deployments?",
        "answer": "Blue-green: two identical environments, switch traffic instantly. Blue = current production, Green = new version. Steps: deploy to green → test green → switch traffic → blue becomes next green. Traffic switch: DNS, load balancer, K8s services. Benefits: instant rollback (switch back), full testing in production-like env. Challenges: database migrations (both versions must work), session management, cost (double resources during deploy). Variations: blue-green with canary (gradual traffic shift). Automate with CI/CD, include smoke tests before switch."
    },
    {
        "question": "What is event-driven architecture in cloud?",
        "answer": "EDA: components communicate through events. Services: Azure Event Grid/Service Bus, AWS EventBridge/SNS/SQS, Cloud Pub/Sub. Patterns: pub/sub, event sourcing, CQRS. Benefits: loose coupling, scalability, async processing. Challenges: eventual consistency, debugging, ordering. Design events: past tense (OrderCreated), include necessary data, versioning. Dead letter queues for failed processing. Idempotent consumers (handle duplicates). Correlation IDs for tracing. Consider: event schema registry, replay capability."
    },
    {
        "question": "How do you implement network segmentation in cloud?",
        "answer": "Network segmentation isolates resources for security. Layers: VNet/VPC level, subnet level, NSG/Security Groups, application level. Patterns: hub-spoke topology, network tiers (web, app, data). Zero trust: verify all traffic, not just perimeter. K8s Network Policies control pod-to-pod traffic. Service mesh for app-layer security (mTLS). Private endpoints for PaaS services. Micro-segmentation: policy per workload. Logging: NSG flow logs, VPC flow logs. Plan carefully: overly strict blocks legitimate traffic."
    },
    {
        "question": "What are SLOs, SLIs, and SLAs?",
        "answer": "SLI (Service Level Indicator): metric measuring service quality. Examples: availability %, latency p99, error rate. SLO (Service Level Objective): target value for SLI. Example: 99.9% availability, p99 latency < 200ms. SLA (Service Level Agreement): contract with consequences. Includes SLOs + penalties for missing. Error budgets: 100% - SLO = acceptable failures. Track SLO burn rate. Alert when burning too fast. Use SLOs for deployment decisions (pause if budget exhausted). Start internal before external SLAs."
    },
    {
        "question": "How do you handle stateful applications in Kubernetes?",
        "answer": "Stateful apps need persistent storage and stable identity. StatefulSets: stable pod names, ordered deployment, persistent volume per pod. Use cases: databases, message queues, distributed systems. PersistentVolumeClaims: request storage from StorageClass. CSI drivers for cloud storage. Challenges: backup (Velero), scaling (data migration), upgrades. Operators: automate day-2 operations (backup, failover). Consider managed services instead (RDS, Cloud SQL). If K8s-hosted: plan for failure, test recovery, understand data durability. Anti-pattern: storing state that belongs in managed service."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "kubectl can't connect to cluster",
        "error_type": "connectivity",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Verify kubeconfig: kubectl config view",
                "Check current context: kubectl config current-context",
                "Test API server: kubectl cluster-info",
                "Check credentials: cloud provider login (az login, aws configure)",
                "Regenerate kubeconfig: az aks get-credentials / aws eks update-kubeconfig",
                "Check VPN/network if private cluster",
                "Verify API server is running in cloud console"
            ],
            "common_causes": [
                "Expired credentials",
                "Wrong kubeconfig context",
                "Network/firewall blocking",
                "Cluster deleted or stopped"
            ]
        }
    },
    {
        "instruction": "Terraform apply fails with resource already exists",
        "error_type": "state_drift",
        "response": {
            "status": "needs_resolution",
            "diagnosis": [
                "Resource exists outside Terraform management",
                "State file out of sync",
                "Another team member created resource"
            ],
            "solutions": [
                "Import existing resource: terraform import TYPE.NAME ID",
                "Remove from state if deleting: terraform state rm TYPE.NAME",
                "Refresh state: terraform refresh",
                "Use data source to reference existing resource instead"
            ],
            "prevention": "Always use Terraform for all infrastructure changes"
        }
    },
    {
        "instruction": "Pods stuck in Pending state",
        "error_type": "scheduling_failure",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "kubectl describe pod <name> - check Events section",
            "common_causes": [
                "Insufficient resources: scale cluster or reduce requests",
                "Node selector/affinity not matched: check node labels",
                "PersistentVolumeClaim pending: check PV availability",
                "Image pull error: verify image exists, check pull secrets",
                "Taints preventing scheduling: check tolerations"
            ],
            "quick_fixes": [
                "kubectl get events --sort-by=.metadata.creationTimestamp",
                "kubectl describe nodes | grep -A5 'Allocated resources'",
                "kubectl get pvc to check volume claims"
            ]
        }
    },
    {
        "instruction": "Delete entire production Kubernetes namespace",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "reason": "This would delete all production resources immediately",
            "impact": [
                "All deployments, pods, services deleted",
                "PersistentVolumeClaims may be deleted (data loss)",
                "No automatic recovery",
                "Potential extended downtime"
            ],
            "alternatives": [
                "Scale deployments to 0 for temporary disable",
                "Use resource protection annotations",
                "Delete specific resources instead",
                "Test in staging first"
            ],
            "if_intentional": "Use kubectl delete namespace --dry-run=client first, then with explicit confirmation"
        }
    },
    {
        "instruction": "Docker build fails with no space left on device",
        "error_type": "resource_exhaustion",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Docker has accumulated images, containers, and build cache",
            "solutions": [
                "docker system prune -a (removes all unused data)",
                "docker builder prune (removes build cache)",
                "docker image prune (removes dangling images)",
                "docker volume prune (removes unused volumes)",
                "Check disk with df -h, clean up other files if needed"
            ],
            "prevention": [
                "Schedule regular docker system prune in CI",
                "Use multi-stage builds to reduce layer count",
                "Set up Docker cleanup policies",
                "Consider larger disk or build agents"
            ]
        }
    },
    {
        "instruction": "ImagePullBackOff error in Kubernetes",
        "error_type": "container_image",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "kubectl describe pod <name> - check image pull error message",
            "common_causes": [
                "Image doesn't exist or wrong tag: verify in registry",
                "Private registry without imagePullSecrets",
                "Registry authentication expired",
                "Network cannot reach registry",
                "Image architecture mismatch (arm64 vs amd64)"
            ],
            "solutions": [
                "Verify image exists: docker pull <image> locally",
                "Create/update imagePullSecrets: kubectl create secret docker-registry",
                "Check secret is referenced in pod spec or service account",
                "For ACR: az acr login or attach ACR to AKS"
            ]
        }
    },
    {
        "instruction": "Terraform state lock error - cannot acquire lock",
        "error_type": "state_locking",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Another terraform process is running or previous run didn't release lock",
            "solutions": [
                "Wait for other process to complete",
                "If stuck: terraform force-unlock LOCK_ID (use carefully!)",
                "Check who holds lock in backend (S3 DynamoDB, Azure Blob)",
                "Verify no CI/CD pipelines running terraform"
            ],
            "warning": "force-unlock can cause state corruption if another process is actually running",
            "prevention": "Use CI/CD serialization for terraform runs"
        }
    },
    {
        "instruction": "Pod CrashLoopBackOff",
        "error_type": "application_crash",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Container starts but crashes repeatedly",
            "debugging_steps": [
                "kubectl logs <pod> - check application logs",
                "kubectl logs <pod> --previous - logs from crashed container",
                "kubectl describe pod <pod> - check exit code and reason",
                "kubectl exec -it <pod> -- /bin/sh - debug if container stays up briefly"
            ],
            "common_causes": [
                "Application error on startup",
                "Missing environment variables or config",
                "Cannot connect to database/dependencies",
                "Liveness probe failing",
                "OOMKilled: increase memory limits"
            ]
        }
    },
    {
        "instruction": "GitHub Actions workflow fails with permission denied",
        "error_type": "ci_cd_permissions",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "GITHUB_TOKEN lacks required permissions",
                "Repository secrets not accessible to forks",
                "Environment protection rules blocking",
                "Missing permissions block in workflow"
            ],
            "solutions": [
                "Add permissions block: permissions: contents: write, packages: write",
                "Check repository Settings > Actions > General",
                "Verify secret names match workflow references",
                "For packages: ensure GITHUB_TOKEN has packages:write"
            ],
            "for_azure": "Check service principal permissions and secret expiry",
            "for_aws": "Verify OIDC provider configuration or access keys"
        }
    },
    {
        "instruction": "Azure deployment fails with quota exceeded",
        "error_type": "quota_limit",
        "response": {
            "status": "needs_resolution",
            "diagnosis": "Resource quota limit reached for subscription/region",
            "solutions": [
                "Check quota: az vm list-usage --location <region>",
                "Request quota increase: Azure Portal > Quotas",
                "Use different VM size or region",
                "Clean up unused resources"
            ],
            "common_quotas": [
                "vCPU limits per region",
                "Public IP addresses",
                "Storage accounts per subscription",
                "VNets per subscription"
            ],
            "prevention": "Plan capacity, request increases before deployment"
        }
    },
    {
        "instruction": "Kubernetes service returns 502 Bad Gateway",
        "error_type": "networking",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Load balancer/ingress cannot reach backend pods",
            "checks": [
                "kubectl get endpoints <service> - are there endpoints?",
                "kubectl get pods -l <selector> - are pods running?",
                "Pod readiness probes passing?",
                "Port numbers match between Service and container?",
                "Network policies blocking traffic?"
            ],
            "common_causes": [
                "No healthy pods to receive traffic",
                "Readiness probe failing (pod not marked ready)",
                "Wrong port configuration",
                "Pod still starting up"
            ]
        }
    },
    {
        "instruction": "Helm upgrade fails with another operation in progress",
        "error_type": "helm_state",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Previous Helm operation didn't complete cleanly",
            "solutions": [
                "Check release status: helm status <release>",
                "If stuck pending: helm rollback <release> <revision>",
                "Last resort: kubectl delete secret -l owner=helm,name=<release>",
                "Then helm upgrade --install"
            ],
            "prevention": [
                "Use --atomic flag for automatic rollback on failure",
                "Use --wait to ensure resources are ready",
                "Set --timeout appropriately"
            ]
        }
    },
    {
        "instruction": "Drop all tables in production database",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "reason": "This would cause immediate and potentially unrecoverable data loss",
            "impact": [
                "All production data deleted",
                "Application failures",
                "Potential compliance violations",
                "Recovery requires backup restore (if available)"
            ],
            "alternatives": [
                "Export data first if migrating",
                "Use separate test database",
                "Truncate specific tables if needed",
                "Test in non-production environment"
            ],
            "if_intentional": "Confirm backup exists and tested, get written approval, schedule maintenance window"
        }
    },
    {
        "instruction": "EKS cluster nodes not joining",
        "error_type": "cluster_node",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Worker nodes cannot register with control plane",
            "checks": [
                "Check node group status in AWS console",
                "Verify IAM role has required policies",
                "Check security groups allow node-to-control-plane",
                "Verify aws-auth ConfigMap has node role mapping",
                "Check VPC/subnet configuration"
            ],
            "common_causes": [
                "aws-auth ConfigMap misconfigured",
                "IAM role missing permissions",
                "Security group blocking traffic",
                "Nodes in wrong subnet"
            ]
        }
    },
    {
        "instruction": "Azure Container Registry push fails with unauthorized",
        "error_type": "authentication",
        "response": {
            "status": "troubleshoot",
            "solutions": [
                "Login to ACR: az acr login --name <registry>",
                "For CI/CD: use service principal or managed identity",
                "Check admin credentials if enabled: az acr credential show",
                "Verify AcrPush role assignment"
            ],
            "for_aks": [
                "Attach ACR to AKS: az aks update --attach-acr",
                "Or use imagePullSecrets with ACR token"
            ],
            "for_github_actions": "Use azure/docker-login action with service principal"
        }
    },
    {
        "instruction": "Terraform plan shows unexpected changes",
        "error_type": "state_drift",
        "response": {
            "status": "investigate",
            "diagnosis": "Infrastructure differs from Terraform configuration",
            "causes": [
                "Manual changes in cloud console",
                "Another pipeline modified resources",
                "Provider version change",
                "State file corruption"
            ],
            "actions": [
                "Review changes carefully - are they expected?",
                "terraform refresh to update state with actual values",
                "If changes are correct: terraform apply to reconcile",
                "If manual change should persist: update config to match"
            ],
            "prevention": "Lock down manual access, use IaC for all changes"
        }
    },
    {
        "instruction": "Kubernetes PersistentVolumeClaim stuck in Pending",
        "error_type": "storage",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "kubectl describe pvc <name> for events",
            "common_causes": [
                "No StorageClass matches request",
                "Insufficient storage capacity",
                "Zone mismatch (PV and pod in different zones)",
                "Cloud provider quota exceeded",
                "WaitForFirstConsumer binding mode"
            ],
            "solutions": [
                "List StorageClasses: kubectl get sc",
                "Check default StorageClass exists",
                "For Azure: ensure disk CSI driver enabled",
                "For AWS: check EBS CSI driver and permissions"
            ]
        }
    },
    {
        "instruction": "GitHub Actions self-hosted runner offline",
        "error_type": "ci_cd_infrastructure",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Check runner machine is running",
                "Verify runner service is started",
                "Check network connectivity to GitHub",
                "Review runner logs in _diag folder",
                "Verify runner registration hasn't expired"
            ],
            "solutions": [
                "Restart runner service",
                "Re-register runner if token expired",
                "Check proxy/firewall settings",
                "Update runner to latest version"
            ],
            "prevention": "Use runner scale sets or ARC for auto-scaling"
        }
    },
    {
        "instruction": "Force push to main branch",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "reason": "Force push rewrites history and can cause data loss",
            "impact": [
                "Collaborators' local copies become invalid",
                "Open PRs may become unmergeable",
                "CI/CD may fail or behave unexpectedly",
                "Audit trail is modified"
            ],
            "alternatives": [
                "git revert for undoing specific commits",
                "Create new branch for experimental work",
                "Use git push --force-with-lease (safer)"
            ],
            "if_intentional": "Notify all team members, ensure no open PRs, consider branch protection rules"
        }
    },
    {
        "instruction": "AWS Lambda function timing out",
        "error_type": "serverless",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Function timeout too low",
                "Cold start taking too long",
                "External service call slow/hanging",
                "Infinite loop or inefficient code",
                "VPC configuration (ENI creation delay)"
            ],
            "solutions": [
                "Increase timeout (max 15 minutes)",
                "For VPC: use VPC endpoints, check NAT gateway",
                "Add timeouts to external calls",
                "Use provisioned concurrency for cold starts",
                "Profile code with X-Ray"
            ],
            "prevention": "Set appropriate timeouts, use async patterns for long operations"
        }
    },
    {
        "instruction": "Kubernetes ingress returns 404",
        "error_type": "networking",
        "response": {
            "status": "troubleshoot",
            "diagnosis": "Request not matching any ingress rule",
            "checks": [
                "kubectl get ingress - verify rules exist",
                "Check host header matches ingress host",
                "Verify path matches (exact vs prefix)",
                "Check ingress controller logs",
                "Verify backend service exists and has endpoints"
            ],
            "common_causes": [
                "Wrong host or path in request",
                "Missing trailing slash in path",
                "Service name typo",
                "Ingress class annotation missing"
            ]
        }
    },
    {
        "instruction": "Terraform destroy entire production infrastructure",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "reason": "This would destroy all managed production resources",
            "impact": [
                "Complete service outage",
                "Potential data loss if resources include databases",
                "DNS records deleted",
                "Networking infrastructure removed",
                "Recovery could take hours or days"
            ],
            "alternatives": [
                "Remove specific resources from state",
                "Use terraform state rm for individual items",
                "Target specific resource: terraform destroy -target",
                "Archive/decommission resources individually"
            ],
            "if_intentional": "Backup everything, document all data, get explicit approval, plan recovery strategy"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(language: str, code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": language,
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    for task in CLOUD_CLI_TASKS + KUBERNETES_TASKS + TERRAFORM_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    return examples

def generate_code_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": ex["instruction"],
        "response": format_code_response(ex["language"], ex["code"], ex["explanation"])
    } for ex in CODE_EXAMPLES]

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Cloud & DevOps Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} CLI/tool examples")
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    print(f"Generated {len(code_examples)} code examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "cloud_devops.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
