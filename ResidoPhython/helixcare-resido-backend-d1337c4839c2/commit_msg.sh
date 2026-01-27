#!/usr/bin/env bash

#current_branch="$(git rev-parse --abbrev-ref HEAD)"

# regex to validate in commit msg
commit_regex='(HXC-[0-9]+|Merge|HDOC-[0-9])'
error_msg="Aborting commit. Your commit message is missing either a user story or an issue number ('HXC-1234' or 'HDOC-1234') or 'Merge'"

if ! grep -iqE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
