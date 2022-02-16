#!/bin/bash
path=$(realpath "$0")
function message {
	chatids=$(cat ${path%/*}/admins.txt | cut -d "{" -f 2 | cut -d '"' -f 2) #text to first id in admins.txt file if bot dies and send log
	for chat_id in $chatids; do
		MESSAGE="$message"
		API_TOKEN=$(cat ${path%/*}/api_token.py | cut -d "'" -f 2)
		/usr/bin/curl -s -o /dev/null -X POST https://api.telegram.org/bot$API_TOKEN/sendMessage -d chat_id="$chat_id" -d text="$message"
	done
}
pid=$(cat ${path%/*}/lostfilm_parcer_bot.py.pidfile)
logfile=" ${path%/*}/lostfilm_parcer_bot.log"
kill -0 $pid; if [ $? != 0 ]
then
	message="pid $pid was found dead, will be restarted"
	message
	API_TOKEN=$(cat ${path%/*}/api_token.py | cut -d "'" -f 2)
	curl -s -o /dev/null -F document=@"$logfile" https://api.telegram.org/bot$API_TOKEN/sendDocument?chat_id=$(cat ${path%/*}/admins.txt | cut -d "{" -f 2 | cut -d '"' -f 2)
	cd ${path%/*}
#	echo > $logfile
	screen -L -Logfile $logfile -A -m -d -S lostfilm_parcer_bot ./lostfilm_parcer_bot.py
fi