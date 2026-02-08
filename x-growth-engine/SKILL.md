---
name: x-growth-engine
description: Fetch X (Twitter) timeline/mentions and generate high-engagement reply drafts for personal and brand growth. Use when the user wants to "check my feed for replies", "grow my twitter following", or "draft engagement replies for sexyvoice".
---

# X Growth Engine

This skill automates the process of finding relevant tweets on your timeline and drafting high-quality, engaging replies to boost your visibility.

## Setup

The skill requires your X Developer credentials:
- `X_BEARER_TOKEN`: For reading public timelines and tweets.
- `X_USER_ID`: Your X numeric User ID.

## Workflow

### 1. Fetching the Timeline
Use the bundled script to get the latest activity:
```bash
# Get your own timeline (or a target user's)
./scripts/fetch_timeline.sh <user_id>
```

### 2. Drafting Replies
Once the tweets are fetched, follow these content strategies for the 10 drafts:

#### For Personal Brand (@gianpaj)
- **The "Builder" Insight**: Add a technical tip or "how-to" related to the tweet.
- **The "Coding Agent" Angle**: Mention how an AI tool (like Claude Code) could solve a problem mentioned in the tweet.
- **The Supportive peer**: Validate a struggle or win from another dev.

#### For SexyVoice.ai
- **The Feature Highlight**: Softly mention how a specific SexyVoice feature (e.g., "ultra-low latency") fits the conversation.
- **The Demo Offer**: "We actually just solved this with our new [Language] model, check it out!"
- **The Industry Thought-Leader**: Share a take on the future of Voice AI.

### 3. Execution
1. Fetch 20 tweets.
2. Select the **top 10** based on engagement potential (high follower count or relevant topic).
3. Draft a unique, non-spammy reply for each.
4. Present the drafts to the user for approval.

## References
- [X API Documentation](https://developer.x.com/en/docs/x-api)
- [Personal Branding Strategies](references/branding.md)
