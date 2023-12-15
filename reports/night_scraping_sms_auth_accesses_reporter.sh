#!/bin/bash

TO_LIST="eric.rodriguez@tesoralia.com,administracion@tesoralia.com,joaquin.fernandez@tesoralia.com,bernardo.ramos@tesoralia.com"
# TO_LIST="david.amor@tesoralia.com"
MAIL_SUBJECT="Tesoralia: ACCESOS CON SMS-AUTH DETECTADO"


FILE=/home/context/logs/night_scraping.log


#2019-09-23 01:05:31:ERROR:EurocajaRuralScraper: DB customer 358682: fin_entity_access 20730: Can't log in. DETECTED REASON: SMS AUTH required
echo > .body
echo "ACCESOS CON SMS-AUTH DETECTADO:" >> .body
echo "===============================" >> .body
cat $FILE | grep "DETECTED REASON: DOUBLE AUTH required" > .tmp
#cat $FILE | grep ":ERROR:CaixaRegularScraper: DB customer" | grep "Can't log in. Unknown reason" > .tmp

while read l
do
	customer=$(echo $l| cut -d" " -f5)
	access=$(echo $l| cut -d" " -f7 |cut -d":" -f1)
	access_row=$(grep "^$access;" accesses.csv)
	customer=$(echo $access_row | cut -d";" -f4)
	#report_row=$(echo $access_row | cut -d";" -f1,3,4,5,6,7,8,9,10,11)
	report_row=$(echo $access_row | cut -d";" -f1,4-12| tr -s ';' ' ')
	
	
	echo "" >> .body
	echo "" >> .body
	echo "$report_row" >> .body 
	echo "$l" >> .body

	
done<.tmp

echo "" >> .body
echo  "----fin----" >> .body
TO=$TO_LIST SUBJECT="$MAIL_SUBJECT "`date +'%d/%m/%Y'` /usr/bin/python3 /home/context/reports/send_report.py

cat .body
