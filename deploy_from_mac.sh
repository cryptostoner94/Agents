#!/usr/bin/env bash
set -e

gcloud compute scp api_main.py install.sh agents-ai-prod:/tmp/ \
  --zone=us-central1-a \
  --project=gen-lang-client-0416088592

gcloud compute ssh agents-ai-prod \
  --zone=us-central1-a \
  --project=gen-lang-client-0416088592 \
  --command 'cd /tmp && bash install.sh'
