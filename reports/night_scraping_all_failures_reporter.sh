#!/bin/bash

TO_LIST="bernardo.ramos@tesoralia.com,eric.rodriguez@tesoralia.com,joaquin.fernandez@tesoralia.com,raul.jimenez@tesoralia.com"
MAIL_SUBJECT="Tesoralia: ACCESOS CON FALLOS SCRAPING NOCTURNO"


FILE=/home/context/logs/night_scraping.log
function put_access {
        while read l
        do
                # Parses
                # 2020-06-23 01:41:17:ERROR:BankinterReceiptsScraper: DB customer 377950: fin_entity_access 21571: Err...
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

}





echo > .body
echo "FALLOS DE CREDENCIALES:" >> .body
echo "=======================" >> .body
cat $FILE | grep "Wrong credentials. Set financial entity inactive" > .tmp
put_access


echo >> .body
echo "ERRORES DE INTEGRIDAD:" >> .body
echo "======================" >> .body
cat $FILE | grep "BALANCE INTEGRITY ERROR:" | grep -v "WARNING" > .tmp
put_access

echo >> .body
echo "ACCESOS CON SMS-AUTH DETECTADO:" >> .body
echo "===============================" >> .body
cat $FILE | grep "DETECTED REASON: DOUBLE AUTH required" > .tmp
put_access





echo "" >> .body
echo  "----fin----" >> .body
TO=$TO_LIST SUBJECT="$MAIL_SUBJECT "`date +'%d/%m/%Y'` /usr/bin/python3 /home/context/reports/send_report.py

cat .body
