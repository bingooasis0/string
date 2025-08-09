start venv - .\venv\Scripts\activate

start frontend - (cd "C:\Users\colby\Desktop\String\frontend") npm run dev
start backend - (cd "C:\Users\colby\Desktop\String\backend") python manage.py runserver
start syslog - (cd "C:\Users\colby\Desktop\String\backend") python manage.py start_syslog
start netflow - (cd "C:\Users\colby\Desktop\String\backend") python manage.py start_netflow




Click the Start Menu and type Windows Defender Firewall.
Open "Windows Defender Firewall with Advanced Security".
In the left pane, click on "Inbound Rules".
In the right pane, click on "New Rule...".
Select "Port" and click Next.
Select "UDP".
Select "Specific local ports" and enter 2055. Click Next.
Select "Allow the connection" and click Next.
Leave all three boxes (Domain, Private, Public) checked and click Next.
Give the rule a name, like String Netflow Collector.
Click "Finish".