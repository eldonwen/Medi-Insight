---
description: Deploy Docker container to Azure Web App
---

# Deploy to Azure Web App

This workflow guides you through deploying your Docker container to Azure Web App for Containers.

## Prerequisites
- Azure CLI installed (`az`)
- Logged in to Azure (`az login`)

## Steps

1. **Create a Resource Group**
   ```bash
   az group create --name MediInsightRG --location eastus
   ```

2. **Create an Azure Container Registry (ACR)**
   ```bash
   az acr create --resource-group MediInsightRG --name mediinsightacr<unique-id> --sku Basic --admin-enabled true
   ```
   *Replace `<unique-id>` with some random numbers to ensure uniqueness.*

3. **Login to ACR**
   ```bash
   az acr login --name mediinsightacr<unique-id>
   ```

4. **Build and Push Docker Image**
   ```bash
   # Get the ACR login server name
   $ACR_SERVER = az acr show --name mediinsightacr<unique-id> --query loginServer --output tsv

   # Tag your local image
   docker tag medi-insight $ACR_SERVER/medi-insight:latest

   # Push to ACR
   docker push $ACR_SERVER/medi-insight:latest
   ```

5. **Create App Service Plan**
   ```bash
   az appservice plan create --name MediInsightPlan --resource-group MediInsightRG --sku B1 --is-linux
   ```

6. **Create Web App**
   ```bash
   az webapp create --resource-group MediInsightRG --plan MediInsightPlan --name medi-insight-app-<unique-id> --deployment-container-image-name $ACR_SERVER/medi-insight:latest
   ```

7. **Configure Environment Variables**
   Set your OpenAI API Key:
   ```bash
   az webapp config appsettings set --resource-group MediInsightRG --name medi-insight-app-<unique-id> --settings OPENAI_API_KEY="your-key-here"
   ```

8. **Verify Deployment**
   Visit `http://medi-insight-app-<unique-id>.azurewebsites.net`
