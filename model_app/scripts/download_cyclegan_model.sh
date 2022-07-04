FILE=$1

echo "Only the following models are available: [\"style_monet\", \"style_cezanne\", \"style_ukiyoe\", \"style_vangogh\"]."

echo "Check the \"$FILE\" model existence."

MODEL_FILE=./checkpoints/${FILE}_pretrained/latest_net_G.pth
URL=http://efrosgans.eecs.berkeley.edu/cyclegan/pretrained_models/$FILE.pth

if [[ -f "$MODEL_FILE" ]]; then
  echo File \""$MODEL_FILE"\" already exists
  else
    mkdir -p ./checkpoints/"${FILE}"_pretrained
    if ! { wget -N "$URL" -O "$MODEL_FILE"; }; then
      rm -rf ./checkpoints/"${FILE}"_pretrained
      echo Style "$FILE" is not available
      return 1
    fi
fi
