#!/bin/bash
# scripts/fetch_timeline.sh

# Requirements: curl, jq
# Env: X_BEARER_TOKEN, X_USER_ID

if [ -z "$X_BEARER_TOKEN" ]; then
    echo "Error: X_BEARER_TOKEN is not set."
    exit 1
fi

# If X_USER_ID is not provided, we can't fetch a private home timeline via Bearer.
# However, we can fetch a USER timeline (public posts) with just a Bearer token.
# To get the HOME timeline (feed), OAuth 2.0 User Token is required.
# For this skill, we'll focus on the USER timeline of the authenticated user or a target.

TARGET_USER_ID=${1:-$X_USER_ID}

if [ -z "$TARGET_USER_ID" ]; then
    echo "Error: No User ID provided and X_USER_ID is not set."
    exit 1
fi

# Fetch the last 20 tweets from the user timeline
# Endpoint: https://api.twitter.com/2/users/:id/tweets
curl -s -X GET "https://api.twitter.com/2/users/${TARGET_USER_ID}/tweets?tweet.fields=created_at,public_metrics,text&expansions=author_id&user.fields=username,name&max_results=20" \
  -H "Authorization: Bearer ${X_BEARER_TOKEN}" | jq .
