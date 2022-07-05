#!/usr/bin/env bash
# use this script to run the model and bot applications

CURR_PATH=$(pwd)

# where to save PIDs of started processes
PID_FILE=$CURR_PATH/pids.txt

# model app
MODEL_APP_PATH=$CURR_PATH/model_app
MODEL_LOADER_SCRIPT=$MODEL_APP_PATH/scripts/download_cyclegan_model.sh
MODEL_APP_MAIN=app.py
PRETRAINED_MODELS=("style_monet" "style_cezanne" "style_ukiyoe" "style_vangogh")

# bot app
BOT_APP_PATH=$CURR_PATH/bot_app
BOT_APP_MAIN=app.py

# kill previously started processes
source stop.sh > /dev/null 2>&1 &
wait
# delete the PIDs file
rm "$PID_FILE" > /dev/null 2>&1

echo Starting model app...

# go to the model app directory
if ! { cd "$MODEL_APP_PATH" 2>/dev/null; }; then
  echo Error! Path to the model app \(\""$MODEL_APP_PATH"\"\) doesn\'t exists
  exit
fi

# download pretrained models if needed
for style in ${PRETRAINED_MODELS[*]}; do
  echo Downloading the \""$style"\" pretrained model
  if ! { source "$MODEL_LOADER_SCRIPT" "$style" > /dev/null 2>&1; }; then
    echo Error! Can\'t download the pretrained model \""$style"\" via \""$MODEL_LOADER_SCRIPT"\"
    exit
  fi
done

# run the model app
if ! { python "$MODEL_APP_MAIN" > /dev/null 2>&1 & }; then
  echo Error! Can\'t run the model app
  exit
else
  MODEL_PID=$!
  echo "$MODEL_PID" > "$PID_FILE"
  echo The model app has been started. PID "$MODEL_PID"
fi

echo Starting the bot app...

# go to the bot directory
if ! { cd "$BOT_APP_PATH" 2>/dev/null; }; then
  echo Error! Path to the bot app \(\""$BOT_APP_PATH"\"\) doesn\'t exists
  kill "$MODEL_PID"
  rm "$PID_FILE"
  exit
fi

# run the bot app
if ! { python "$BOT_APP_MAIN" > /dev/null 2>&1 & }; then
  echo Error! Can\'t run the bot app
  kill "$MODEL_PID"
  rm "$PID_FILE"
  exit
else
  BOT_PID=$!
  echo "$BOT_PID" >> "$PID_FILE"
  echo The bot app has been started. PID "$BOT_PID"
fi

echo All services have been started

cd "$CURR_PATH"
