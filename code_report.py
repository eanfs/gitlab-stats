# encoding: utf8
import os
import json
import datetime
import requests
import smtplib
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

FROM_ADDR = 'yuchuan.wang@bespinglobal.cn'
FROM_PASS = 'Vancl@123'
TO_ADDR = 'yuchuan.wang@bespinglobal.cn'
SMTP_SERVER = 'mail.bespinglobal.cn'
SMTP_PORT = 587

token = "xAf2n2JZsT2YaYrz3qGC"
base_url = "https://git.opsnow.tech/api/v4"
cur_date = datetime.datetime.now()
#pre_date = (cur_date).strftime("%Y-%m-%d")
pre_date = "2019-07"
#since_date = (cur_date - datetime.timedelta(days=2)).strftime("%Y-%m-%d 22:00:00")
#until_date = (cur_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d 22:00:00")
#until_date = cur_date.strftime("%Y-%m-%d 22:00:00")
since_date = "2019-08-05 00:00:00"
until_date = "2019-08-12 00:00:00"
project_result = {}

def get_data(url):
    headers = {
        "PRIVATE-TOKEN": token
    }

    rs = []

    try:
        r = requests.get(url, headers=headers)

    except Exception as e:
        print(e)

    else:
        rs = r.json()

        return rs


#http://git.opsnow.tech/api/v4/groups/47/issues\?state\=opened
# /projects/:id/issues
def get_issue_by_projectid(project_id):
    url = "%s/projects/%s/issues?per_page=2000" % (base_url, project_id)
    return get_data(url)


# /projects
def get_projects():
    url = "%s/projects?per_page=2000" % base_url
    rs = get_data(url)

    result = {"BP-CMP": [], "BP-BILLING": [], "BP-MONITOR": [], "BP-AUTOMATE": [], "BP-FRONT-END": [], "BP-CMDB": [], "BP-TICKET": [], "BP-IAM": [], "BP-NOTIFIER": []}
    for p in rs:
        for k in result.keys():
            if p['namespace']['full_path'].startswith('PD/Private2.0/%s' % k):
                result[k].append({"id": p['id'], "name": p['name'], "ssh_url_to_repo": p['ssh_url_to_repo']})
                break

    return result


def get_project_code_count(project_name, name, path):
    if os.path.exists(name):
        a = os.system('cd %s;git pull' % name)
        if a != 0:
            os.system('rm -rf %s' % name)
            a = os.system('git clone %s %s' % (path, name))

    else:
        a = os.system('git clone %s %s' % (path, name))

    if a != 0:
        print("git clone %s error" % path)
        return

    a = os.system('cd %s;git checkout master;git pull origin master' % name)
    if a != 0:
        print("checkout master error for %s" % name)
        return

    cmd = """cd %s;git log --since=="%s" --until=="%s" """ % (name, since_date, until_date)
    cmd += """--format='%ae' --date=local | sort -u | while read name; do echo "$name:"; """
    cmd += """git log --since=="%s" --until=="%s" """ % (since_date, until_date)
    cmd += """ --date=local --author="$name" --pretty=tformat: --numstat | awk '{ add += $1; """
    cmd += """subs += $2; loc += $1 - $2 } END { printf "%s:%s;", add, subs}' -; done"""

    cmd2 = 'cd %s;' % name + 'git log --pretty=%ae '
    cmd2 += '--since=="%s" --until=="%s" | sort | uniq -c | sort -k1 -n -r' % (since_date, until_date)

    master_rs = os.popen(cmd).read()

    rs = {}
    subs_rs = {}
    if master_rs.strip():
        for i in master_rs.strip().strip(';').replace('\n', '').split(';'):
            user, num, subs = i.split(':')
            if num:
                rs[user.split('@')[0]] = int(num)

            if subs:
                subs_rs[user.split('@')[0]] = int(subs)

    master_commit_rs = os.popen(cmd2).read()

    commit_rs = {}
    if master_commit_rs:
        print(master_commit_rs)
        for i in master_commit_rs.strip().split('\n'):
            print(i)
            num, user = i.strip().split()
            if num:
                commit_rs[user.split('@')[0]] = int(num)

    for b in ['dev', 'ocenter', 'alarm']:
        a = os.system('cd %s;git checkout %s;git pull origin %s' % (name, b, b))
        if a == 0:
            dev_rs = os.popen(cmd).read()
            if dev_rs.strip():
                for i in dev_rs.strip().strip(';').replace('\n', '').split(';'):
                    user, num, subs = i.split(':')
                    u = user.split('@')[0]
                    print(user, num, subs)
                    if num:
                        if u not in rs or rs[u] < int(num):
                            rs[u] = int(num)

                    if subs:
                        if u not in subs_rs or subs_rs[u] < int(subs):
                            subs_rs[u] = int(subs)

            dev_commit_rs = os.popen(cmd2).read()
            if dev_commit_rs.strip():
                for i in dev_commit_rs.strip().split('\n'):
                    num, user = i.strip().split()
                    print("commit:", user, num)
                    if num:
                        u = user.split('@')[0]
                        if u not in commit_rs or commit_rs[u] < int(num):
                            commit_rs[u] = int(num)


    for k, v in rs.items():
        if k in project_result[project_name]['members']:
            project_result[project_name]['members'][k]['today_code_line'] += v

    for k, v in subs_rs.items():
        if k in project_result[project_name]['members']:
            project_result[project_name]['members'][k]['today_subs_line'] += v

    for k, v in commit_rs.items():
        if k in project_result[project_name]['members']:
            project_result[project_name]['members'][k]['today_commit'] += v


def parse_issues(issues, project_name):
    for issue in issues:
        parse_issue(issue, project_name)


def parse_issue(issue, project_name):
    username = ""
    if issue['assignee']:
        username = issue['assignee']['username']
        if project_name == 'BP-AUTOMATE' and username in ['cairong.li', 'zan.li', 'zhiqiang.qian']:
            username = ""

        else:
            if username not in project_result[project_name]['members']:
                project_result[project_name]['members'][username] = {
                    "name": issue['assignee']['name'],
                    "total": 0,
                    "today_add_feat": 0,
                    "today_add_bug": 0,
                    "today_done": 0,
                    "today_delay": 0,
                    "today_code_line": 0,
                    "today_subs_line": 0,
                    "today_commit": 0
                }

    if issue['state'] == "closed":
        if not issue['closed_at'].startswith(pre_date):
            return

        project_result[project_name]['today_done'] += 1
        if username:
            project_result[project_name]['members'][username]['today_done'] += 1

    else:
        project_result[project_name]['total'] += 1
        if username:
            project_result[project_name]['members'][username]['total'] += 1

        if issue['created_at'].startswith(pre_date):
            if 'Bug' in issue['labels']:
                project_result[project_name]['today_add_bug'] += 1
                if username:
                    project_result[project_name]['members'][username]['today_add_bug'] += 1

            else:
                project_result[project_name]['today_add_feat'] += 1
                if username:
                    project_result[project_name]['members'][username]['today_add_feat'] += 1

        if issue['due_date'] and (cur_date - datetime.datetime.strptime(issue['due_date'], '%Y-%m-%d')).days > 1:
            project_result[project_name]['today_delay'] += 1
            if username:
                project_result[project_name]['members'][username]['today_delay'] += 1


def gen_html():
    total = {
        "total": 0,
        "today_add_feat": 0,
        "today_add_bug": 0,
        "today_done": 0,
        "today_delay": 0,
        "today_code_line": 0,
        "today_subs_line": 0,
        "today_commit": 0
    }

    project_fields = [u"项目名称", u"姓名", u"未完成任务总数", u"今日新增需求总数", u"今天新增Bug总数", u"今日完成任务总数",
                      u"今日延期任务总数", u"今日代码新增总数", u"今日代码删除总数", u"今日代码提交次数"]
    keys = ["total", "today_add_feat", "today_add_bug", "today_done", "today_delay",
            "today_code_line", "today_subs_line", "today_commit"]
    colors = ["blue", "green", "red", "blue", "red", "blue", "blue", "blue"]

    html_title = u'<table border="1" bordercolor="#96beee" style="border-collapse:collapse;"><tr>'
    for i in project_fields:
        html_title += u'<th style="background-color:#c0d5f0">%s</th>' % i
    html_title += u'</tr>'

    html = u''
    for k, v in sorted(project_result.items(), key=lambda item:item[0]):
        html += u'<tr><th rowspan="%s">%s</th>' % (len(project_result[k]['members'].keys()) + 1, k)
        html += u'<th>Total</th>'

        for i in range(len(keys)):
            html += u'<th>%s</th>' % \
                    ('<font style="color:%s">%s</font>' % (colors[i], v[keys[i]]) if v[keys[i]] > 0 else '')
        html += u'</tr>'

        for m, n in sorted(project_result[k]['members'].items(), key=lambda item:item[0]):
            html += u'<tr><th>%s</th>' % (n['name'])

            for i in range(len(keys)):
                html += u'<th>%s</th>' % \
                        ('<font style="color:%s">%s</font>' % (colors[i], n[keys[i]]) if n[keys[i]] > 0 else '')
            html += u'</tr>'

        for i in total.keys():
            total[i] += v[i]

    html += u'</table>'

    html_total = u'<tr><th>总计</th><th></th>'
    for i in range(len(keys)):
        html_total += u'<th>%s</th>' % \
                ('<font style="color:%s">%s</font>' % (colors[i], total[keys[i]]) if total[keys[i]] > 0 else '')
    html_total += u'</tr>'

    return html_title + html_total + html


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))

def send_mail(text):

    msg = MIMEText(u'<html><body>' +
        u'%s' % text +
        u'<br><hr><div style="color:silver;font-style:italic">此邮件由系统自动发送，请勿回复</div>'
        u'</body></html>', 'html', 'utf-8')
    msg['From'] = _format_addr(u'<%s>' % FROM_ADDR)
    msg['To'] = _format_addr(u'<%s>' % TO_ADDR)
    msg['Subject'] = Header(u'%s-研发工作量统计' % pre_date, 'utf-8').encode()

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    # server.set_debuglevel(1)
    server.login(FROM_ADDR, FROM_PASS)
    server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    server.quit()



def main():
    projects = get_projects()

    for k, v in projects.items():
        if k not in project_result:
            project_result[k] = {
                "total": 0,
                "today_add_feat": 0,
                "today_add_bug": 0,
                "today_done": 0,
                "today_delay": 0,
                "today_code_line": 0,
                "today_subs_line": 0,
                "today_commit": 0,
                "members": {}
            }

        for p in v:
            issues = get_issue_by_projectid(p['id'])
            parse_issues(issues, k)

        for p in v:
            get_project_code_count(k, p['name'], p['ssh_url_to_repo'])

    # print project_result
    # print json.dumps(project_result)
    for k, v in project_result.items():
        for m, n in v['members'].items():
            project_result[k]['today_code_line'] += n['today_code_line']
            project_result[k]['today_subs_line'] += n['today_subs_line']
            project_result[k]['today_commit'] += n['today_commit']

    for k in project_result.keys():
        if project_result[k]['today_code_line'] == 0:
            del project_result[k]

    for k in project_result.keys():
        for m in project_result[k]['members'].keys():
            if project_result[k]['members'][m]['today_code_line'] == 0:
                del project_result[k]['members'][m]

    while True:
        try:
            send_mail(gen_html())

        except Exception as e:
            print("send mail fail: %s, retry..." % e)
            continue

        break


if __name__ == "__main__":
    main()
    #print json.dumps(get_projects())
