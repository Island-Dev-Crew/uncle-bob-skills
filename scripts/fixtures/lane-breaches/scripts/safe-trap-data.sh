#!/usr/bin/env bash
# Exit: 0 always. Mentioning a client name as data, or printing trap state,
# does not schedule the network client for execution.
trap 'printf "%s\n" curl' EXIT
trap -p
