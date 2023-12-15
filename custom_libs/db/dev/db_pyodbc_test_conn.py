import pyodbc

"""
$ sudo apt-get install unixodbc unixodbc-dev
$ pip3 install pyodbc
$ sudo sh -c 'echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/mssql-ubuntu-xenial-release/ xenial main" > /etc/apt/sources.list.d/mssqlpreview.list'
$ sudo apt-key adv --keyserver apt-mo.trafficmanager.net --recv-keys 417A0893

$ sudo apt install libodbc1-utf16
$ sudo apt install msodbcsql unixodbc-dev-utf16
"""

conn_str = 'Driver={ODBC Driver 13 for SQL Server};Server=tcp:tesoralia.database.windows.net,1433;Database=lportal;Uid=tesoraliaService;Pwd=kCPVHi0kbv6bw4c3wbzmCHMsBo/dH5sRWS4krWq1Vfg=;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
with pyodbc.connect(conn_str) as conn:

    cursor = conn.cursor()
    cursor.execute('EXEC dbo.Customer @CustomerId = Null')

    rows = cursor.fetchall()
    for row in rows:
        print(row)



