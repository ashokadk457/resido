#!/bin/bash
MAJOR_VERSION="1"
MINOR_VERSION="32"

git fetch --all
current_branch=$(git rev-parse --abbrev-ref HEAD)


function create_release_branch_using_major_minor() {
    new_release="release/$MAJOR_VERSION.$MINOR_VERSION"
    git checkout -b $new_release
    git push origin $new_release
    echo "Created release $new_release"
}

function create_release_branch() {
    if [ "$current_branch" == "main" ]
    then
        create_release_branch_using_major_minor
    else
        echo "Cannot create a release from $current_branch branch"
    fi
}


create_release_branch
