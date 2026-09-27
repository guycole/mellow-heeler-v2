#!/bin/bash
#
# Title:genesis.sh
# Description:
# Development Environment: OS X 12.7.6/postgres 15.8
#
psql -U postgres template1 (or psql -U gsc template1)

# (mac) user
createuser -U gsc -d -e -l -P -r -s heeler_admin
woofwoof
createuser -U gsc -e -l -P heeler_client
batabat

# (linux) su - postgres
createuser -U postgres -d -e -l -P -r -s heeler_admin
woofwoof
createuser -U postgres -e -l -P heeler_client
batabat

#createdb heeler -O heeler_admin -D heeler -E UTF8 -T template0 -l C
createdb heeler -O heeler_admin -E UTF8 -T template0 -l C

# psql -h localhost -p 5432 -U heeler_admin -d heeler
# psql -h localhost -p 5432 -U heeler_client -d heeler
