#! /usr/bin/env bash

for name in members encodings ; do
  if [ ! -f "${name}.db" ] ; then
    sqlite3 "${name}.db" < "${name}.schema"
  fi
  if [ "$name" == "members" ] ; then
    table="members"
  else
    table="cards"
  fi
  sqlite3 "${name}.db" ".schema $table"
done

