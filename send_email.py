import mimetypes
import os
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from util.common import Conf


class Sendemail:
    def __init__(self):
        conf = Conf()
        self.host_server = conf.getconf("Email").host_server
        self.port = conf.getconf("Email").host_port
        self.sender_email = conf.getconf("Email").sender_email
        self.sender_pwd = conf.getconf("Email").sender_pwd
        self.receiver = conf.getconf("Email").receiver
        self.ccer = conf.getconf("Email").ccer
        self.att=conf.getconf("Email").att

    def send_email(self, title, body_text):
        try:
            smtp = SMTP_SSL(self.host_server, self.port)
            smtp.login(self.sender_email, self.sender_pwd)  # 登陆
            msg = MIMEMultipart()
            msg['Subject'] = Header(title)  # 主题
            msg['From'] = self.sender_email  # 发件人
            msg['To'] = self.receiver  # 收件人
            msg['Cc'] = self.ccer  # 抄送
            msg.attach(MIMEText(body_text, 'html'))  # 正文

            #添加附件
            for filename in self.att.split(','):
                if filename != None and os.path.exists(filename):
                    ctype, encoding = mimetypes.guess_type(filename)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/", 1)
                    attachment = MIMEImage((lambda f: (f.read(), f.close()))(open(filename, "rb"))[0], _subtype = subtype)
                    attachment.add_header("Content-Disposition", "attachment", filename = filename.split('/')[len(filename.split('/'))-1])
                    msg.attach(attachment)

            smtp.sendmail(self.sender_email, self.receiver.split(','), msg.as_string())  # 发送邮件
            smtp.quit()  # 结束会话

        except Exception as error:
            print(error)


if __name__ == '__main__':
    title = "内核自动化测试报告"
    mail_txt = "<p>点链接查看详细测试结果</p>http://10.20.33.147:43005/index.html#behaviors</p>"
    # mail_txt = "111111"
    sdm = Sendemail()
    sdm.send_email(title, mail_txt)




