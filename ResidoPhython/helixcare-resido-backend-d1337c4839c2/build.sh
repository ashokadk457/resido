#!/bin/bash
set -e
IMAGE_REPO="helix.azurecr.io/resido-backend"
REPO_DIR="."
RELEASE_NAME="resido-backend"
CHART_NAME="resido-backend"

# Function to print usage
usage() {
    echo "Usage: $0 <tag>"
    exit 1
}

# Check if tag is provided
if [ -z "$1" ]; then
    usage
fi
cd "${REPO_DIR}"

# Get the input tag
TAG=$1
ENV=$2
deployment_id=$3
silent=$4
SANITIZED_TAG=$(echo "$TAG" | tr -d '/:')
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

is_semantic_version() {
  [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*)?$ ]]
}

WEBHOOK_URL="https://prod-189.westus.logic.azure.com:443/workflows/4bb58b1bb35d4ebd934e5fb019a40115/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=_rwAU4MoUY77DdiGjioX4-mFONACmtLDcOoKg9-dm9Y"   # PULSE RELEASES CHANNEL

notify_teams() {
  local message="$1"

  curl --location "$WEBHOOK_URL" \
    --header 'Content-Type: application/json' \
    --data "{
      \"type\": \"message\",
      \"attachments\": [
        {
          \"contentType\": \"application/vnd.microsoft.card.adaptive\",
          \"content\": {
            \"type\": \"AdaptiveCard\",
            \"body\": [
              {
                \"type\": \"TextBlock\",
                \"text\": \"$message\",
                \"wrap\": true
              },
              {
                \"type\": \"TextBlock\",
                \"text\": \"Component: BE\",
                \"wrap\": true
              },
              {
                \"type\": \"TextBlock\",
                \"text\": \"ENV: \`$ENV\`\",
                \"wrap\": true
              },
              {
                \"type\": \"TextBlock\",
                \"text\": \"Version: \`$TAG\`\",
                \"wrap\": true
              },
              {
                \"type\": \"TextBlock\",
                \"text\": \"Deployment ID: \`$deployment_id\`\",
                \"wrap\": true
              }
            ],
            \"\$schema\": \"http://adaptivecards.io/schemas/adaptive-card.json\",
            \"version\": \"1.0\"
          }
        }
      ]
    }"
}

if [[ "$silent" != "--silent" ]]; then
  notify_teams "Deployment Started"
fi

# Fetch all tags from the repository
git fetch --tags
git fetch --all

# Check if the tag exists
git checkout "$TAG"
git pull origin "$TAG"

docker login helix.azurecr.io --username helix --password V4tcaCRc5RzbbKARZmp4NdQBzC4V84Akc0vO2NXlrQ+ACRCZZRQH

# Build the Docker image with the same tag
docker build -t ${IMAGE_REPO}:"$SANITIZED_TAG" -f Dockerfile . --platform=linux/amd64
docker push ${IMAGE_REPO}:"$SANITIZED_TAG"

echo "Docker image built with tag: $SANITIZED_TAG"

if is_semantic_version "$TAG"; then
  echo "Semantic version detected: $TAG"
  CHART_VERSION=$SANITIZED_TAG
else
  CHART_VERSION="0.1.1-${SANITIZED_TAG}"
  echo "Non-semantic version, using chart version: $CHART_VERSION"
fi

echo "Building Chart with version: $CHART_VERSION"
helm package charts --version ${CHART_VERSION}
helm push ${CHART_NAME}-${CHART_VERSION}.tgz oci://helix.azurecr.io/helm


if [ "$ENV" == "dev" ]; then
    echo "Deployment Started on dev env"
    sudo helm upgrade $RELEASE_NAME oci://helix.azurecr.io/helm/${CHART_NAME} -n pulse-dev --reuse-values --set image.tag=$SANITIZED_TAG --set podAnnotations.deployedAt=${TIMESTAMP}-ui --kube-context qa --version=$CHART_VERSION --wait
    if [[ "$silent" != "--silent" ]]; then
      notify_teams "Deployment Completed"
    fi
elif [ "$ENV" == "qa" ]; then
    echo "Deployment Started on QA env"
    sudo helm upgrade $RELEASE_NAME oci://helix.azurecr.io/helm/${CHART_NAME} -n pulse --reuse-values --set image.tag=$SANITIZED_TAG --set podAnnotations.deployedAt=${TIMESTAMP}-ui --kube-context qa --version=$CHART_VERSION --wait
    if [[ "$silent" != "--silent" ]]; then
      notify_teams "Deployment Completed"
    fi
elif [ "$ENV" == "demo" ]; then
    echo "Environment is DEMO"
    sudo helm upgrade $RELEASE_NAME oci://helix.azurecr.io/helm/${CHART_NAME} -n pulse --reuse-values --set image.tag=${SANITIZED_TAG} --set podAnnotations.deployedAt=${TIMESTAMP}-ui --kube-context demo --version=$CHART_VERSION --wait
    if [[ "$silent" != "--silent" ]]; then
      notify_teams "Deployment Completed"
    fi
elif [ -z "$ENV" ]; then
    echo "Environment is not defined - skipping deployment"
    if [[ "$silent" != "--silent" ]]; then
      notify_teams "Deployment Skipped"
    fi
fi
