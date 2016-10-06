#!/bin/bash

if [ "$#" -ne 3 ];
   then
   echo "You must provide 3 parameters:"
   echo "[url] [docker image] [num request per experiment]"
   exit 1
fi

declare -a arr=("alice" "atlas" "cms" "lhcb" "recast")

for i in "${arr[@]}";
do
  for j in $(eval echo "{1..$3}");
  do
      curl -sL --data "docker-img=$2&weight=fast&experiment=$i&input-file=7,45,345,76" $1 > /dev/null;
  done;
  echo "$3 requests for executing $2 were sent to $1 on $i infrastructure"
done;
