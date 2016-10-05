#!/bin/bash

if [ "$#" -ne 3 ];
   then
   echo "You must provide 3 parameters:"
   echo "[url] [number to calculate fibonacci] [number of request per experiment]"
   exit 1
fi

declare -a arr=("alice" "atlas" "cms" "lhcb")

for i in "${arr[@]}";
do
  for j in $(eval echo "{1..$3}");
  do
      curl -sL --data "number=$2&experiment=$i&submit=Submit" $1 > /dev/null;
  done;
  echo "$3 requests for calculating fibonacci of $2 were sent to $1 on $i infrastructure"
done;
