#!/bin/bash

silent=$1

git fetch --tags
# git pull

current_branch=$(git rev-parse --abbrev-ref HEAD)
versions_file_path="./common/version.txt"

get_currently_deployed_version() {
  local version_url="$1"
  local deployed_version

  deployed_version=$(curl -s --location "$version_url" | grep '"version"' | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')

  echo "$deployed_version"
}

function create_tag_on_release_branch() {
    MAJOR_MINOR=${current_branch##*/}

    if [[ "$current_branch" == "develop" ]]
    then
        full_tag_prefix="$MAJOR_MINOR"
        VERSION_URL="http://resido-dev.helixbeat.com/api/v1/versions"
    else
        full_tag_prefix="v$MAJOR_MINOR"
        VERSION_URL="http://resido-qa.helixbeat.com/api/v1/versions"
    fi
    last_tag=$(git tag --sort=-"v:refname" | grep ^"${full_tag_prefix}" | head -n 1)
    echo "Last created tag on $current_branch : $last_tag"

    last_patch=${last_tag##*.}
    new_patch_number=$((last_patch+1))
    new_tag="${full_tag_prefix}.${new_patch_number}"
    echo "Creating new tag: $new_tag"
    printf "\n"

    rm "$versions_file_path"
    current_release_time=$(date)
    version_update_string="version=$new_tag"
    branch_update_string="release=$current_branch"
    built_on_string="built_on=$current_release_time"
    echo "$version_update_string" >> "$versions_file_path"
    echo "$branch_update_string" >> "$versions_file_path"
    echo "$built_on_string" >> "$versions_file_path"
    git add "$versions_file_path"
    git commit -m"Merge: Updating version to $new_tag"

    git tag "$new_tag"
    git push origin "$new_tag"
    git push origin "$current_branch"

    CURRENTLY_DEPLOYED_VERSION=$(get_currently_deployed_version "$VERSION_URL")
    echo "Currently deployed version: $CURRENTLY_DEPLOYED_VERSION"

    ./get_diff.sh "$CURRENTLY_DEPLOYED_VERSION" "$new_tag" "$silent"
}



if [[ "$current_branch" =~ ^release/[0-9] || "$current_branch" == "develop" ]]
then
    create_tag_on_release_branch
else
    echo "Cannot create tag"
fi
