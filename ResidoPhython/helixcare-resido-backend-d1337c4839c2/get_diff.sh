#!/bin/bash
old=$1
new=$2
silent=$3

new_tag_commit_hash=$(git rev-list -n 1 "$new")
new_tag_author=$(git show -s --format='%an <%ae>' "$new_tag_commit_hash")

ENG_WEBHOOK_URL="https://prod-70.westus.logic.azure.com:443/workflows/f51a4d7722674872bbc17f4565432d34/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=XXfUiJJ7CLpkANLuaTrKloczeuloQo3j_TcGELde9Eo"  # Engineering Channel Workflow URL
REL_WEBHOOK_URL="https://prod-189.westus.logic.azure.com:443/workflows/4bb58b1bb35d4ebd934e5fb019a40115/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=_rwAU4MoUY77DdiGjioX4-mFONACmtLDcOoKg9-dm9Y" # PULSE Releases Channel Workflow URL

send_to_teams_if_needed() {
    local old="$1"
    local new="$2"
    local silent="$3"
    local header_string="$4"
    local full_jira_diff_string="$5"
    local full_git_diff_string="$6"
    local author_string="$7"

    if [[ "$silent" != "--silent" ]]; then
        if [[ "$old" == develop* && "$new" == develop* ]]; then
            webhook_url=$ENG_WEBHOOK_URL
        elif [[ "$old" == v* && "$new" == v* ]]; then
            webhook_url=$REL_WEBHOOK_URL
        else
            echo "Tag names do not match expected format. Not sending to Teams."
            return
        fi

        curl --location "$webhook_url" \
          --header "Content-Type: application/json" \
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
                      \"text\": \"New PULSE BE Build ${new}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"${header_string}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"${author_string}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"${full_jira_diff_string}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"${full_git_diff_string}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"${header_string}\",
                      \"wrap\": true
                    },
                    {
                      \"type\": \"TextBlock\",
                      \"text\": \"Please approve for Deployment.\",
                      \"wrap\": true
                    }
                  ],
                  \"\$schema\": \"http://adaptivecards.io/schemas/adaptive-card.json\",
                  \"version\": \"1.0\"
                }
              }
            ]
          }"
        echo "Sent diff to Teams channel."
    else
        echo "Silent flag detected. Skipping Teams message."
    fi
}

echo "Generating diff between old: $old and new: $new"
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Current Branch: $current_branch"
echo "Fetching and pulling latest $old and latest $new"
git fetch
git checkout "$old"
git pull origin "$old"
git checkout "$new"
git pull origin "$new"

GIT_LOG_LIST=$(git log $old..$new --oneline --no-merges --grep="^RPM" --pretty=format:"%s")
BASE_HDOC_JIRA_URL="https://helixbeat.atlassian.net/jira/software/c/projects/RPM/issues?jql=id%20in%20"
jira_tickets_list_rpm=()
for commit_log in "${GIT_LOG_LIST[@]}"; do
    jira_tag="$( cut -d ' ' -f 1 <<< "$commit_log" )"
    jira_tag_stripped=${jira_tag%$'\n'}

    if [[ "$jira_tag_stripped" == RPM* ]]; then
        jira_tickets_list_rpm+=("$jira_tag_stripped")
    fi
done
unique_jira_ids_hdoc=($(echo "${jira_tickets_list_rpm[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

jira_diff_hdoc="("
for val in "${unique_jira_ids_hdoc[@]}"; do
    jira_diff_hdoc=("$jira_diff_hdoc$val%2C")
done
jira_diff_hdoc="${jira_diff_hdoc%???})"
full_jira_diff_hdoc="${BASE_HDOC_JIRA_URL}${jira_diff_hdoc}"

full_jira_diff_string="JIRA DIFF: ${full_jira_diff_hdoc}"
#full_git_diff_string="GIT DIFF: https://sourcecode.helixbeat.com/root/helixBackend/compare/$old...$new"
full_git_diff_string="GIT DIFF: https://bitbucket.org/helixcare/resido-backend/branches/compare/$new%0D$old"
header_string="********* BE ${old} → BE ${new} *********"
author_string="CREATED BY: ${new_tag_author}"

echo "${header_string}"
#echo "JIRA Diff (Project HDOC):"
#echo "${full_jira_diff_hdoc}"
echo "${author_string}"
echo "${full_jira_diff_string}"
echo "${full_git_diff_string}"
#printf "\n"
#echo "JIRA Diff (Project HXC):"
#echo "${full_jira_diff_hxc}"
#printf "\n"
#echo "GIT Diff:"
#echo "${full_git_diff_string}"
echo "${header_string}"
echo "Switching back to $current_branch"
git checkout "$current_branch"
# send_to_teams_if_needed "$old" "$new" "$silent" "$header_string" "$full_jira_diff_string" "$full_git_diff_string" "$author_string"
