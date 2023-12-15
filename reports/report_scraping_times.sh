#!/bin/bash

LOGFILE=/home/context/logs/night_scraping.log
#LOGFILE=main_launcher__2019_09_22__23_00_02.log

FINISH=$(cat $LOGFILE | grep "INFO:main_launcher_receipts._process_scraper: DB customer"| grep -v "fin_entity_access ALL:" | grep "fin_entity" | grep "of fin_entity"| grep "finish" | sort -n -k5)
DATE=`date +%Y%m%d`

REPORTFILE="night_scraping_report_$DATE.csv"
SHARED_DEST="/mnt/tesoralia/prod/reports/"


echo "CUSTOMER ID;ACCESO;FINENT ID;COMIENZO;FINAL;TIEMPO;ESTADO" > $REPORTFILE

count=0
while read l
do
	(( count++ ))
	if ((count%1000 == 0))
	then
		echo "$count lines processed"
	fi

	start=${l:0:19}
	if [[ ! $start =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}.[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]
	then
		continue
	fi

	customer=$(echo $l| cut -d" " -f5 | cut -d":" -f1)
	access=$(echo $l| cut -d" " -f7)
	finent=$(echo $l| cut -d" " -f10 | cut -d":" -f1)

	finish=$(echo "$FINISH" | grep "INFO:main_launcher_receipts._process_scraper: DB customer" |  grep "finish" | grep -F "$customer" | grep -F "$access"| grep -F "$finent" |  cut -d":" -f1-3)
	if [ "$finish" == "" ]
	then
		echo "$customer;$access;$finent;$start;$finish;;NO TERMINADO;" >> $REPORTFILE
		continue	
	fi
	start_epoch=$(date --date="$start" +"%s")	
	finish_epoch=$(date --date="$finish" +"%s")
	delta_seconds=$(( $finish_epoch - $start_epoch ))
	echo "$customer;$access;$finent;$start;$finish;$delta_seconds;OK;" >> $REPORTFILE
	
done<$LOGFILE

mv $REPORTFILE $SHARED_DEST
echo "DONE!"
