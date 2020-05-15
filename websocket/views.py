from django.shortcuts import render
from dwebsocket.decorators import accept_websocket, require_websocket
from django.http import HttpResponse
import paramiko
import psutil
import time

#C
@accept_websocket
def echo_once(request):
    if not request.is_websocket():  # 判断是不是websocket连接
        try:  # 如果是普通的http方法
            message = request.GET['message']
            return HttpResponse(message)
        except:
            return render(request, 'index.html')
    else:
        for message in request.websocket:
            message = message.decode('utf-8')  # 接收前端发来的数据
            print(message)
            if message == 'backup_all':#这里根据web页面获取的值进行对应的操作
                command = 'bash /root/ping.sh'#这里是要执行的命令或者脚本

                # 远程连接服务器
                hostname = '172.16.2.225'
                username = 'root'
                password = '123456'

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=hostname, username=username, password=password)
                # 务必要加上get_pty=True,否则执行命令会没有权限
                stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
                # result = stdout.read()
                # 循环发送消息给前端页面
                while True:
                    nextline = stdout.readline().strip()  # 读取脚本输出内容
                    #print(nextline.strip())
                    request.websocket.send(nextline) # 发送消息到客户端
                    # 判断消息为空时,退出循环
                    if not nextline:
                        break
                ssh.close()  # 关闭ssh连接
            elif message =="stop_cmd":
                kill_process_with_name("ping")
                request.websocket.send("任务已停止！")  # 发送消息到客户端
                ssh.close()
            else:
                request.websocket.send('没权限!!!'.encode('utf-8'))

def kill_process_with_name(process_name):
    pid_list = psutil.pids() #遍历所有进程
    for pid in pid_list:
        try:
            each_pro = psutil.Process(pid)
            if process_name.lower() in each_pro.name().lower():
                #print("进程是%s，pid是%s" % (each_pro.name(),each_pro.pid))
                time.sleep(1)
                # 杀死父子进程
                parent_pid = each_pro.pid
                parent = psutil.Process(parent_pid)
                for child in parent.children(recursive=True):  # or parent.children() for recursive=False
                    child.kill()
                parent.kill()
                break
        except Exception as ret:
            print(ret)