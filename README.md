# Zabbix_Temple
Zabbix_Template
1）导入Mongodb的模版（模版下载：Templates_Mongodb.xml）
2）添加到主机并链接模版
3）修改模版监控项中的详细信息，把之前28018改成现在mongodb的端口即可~ 否则会一直报警。因为模版中默认监控的的端口是28018.
4）在模版中，选择Template MongoDB模版，然后批量更新，改成zabbix客户端监控~
5）修改成功之后，可以在最新数据中查看状态为1，就是运行中~
