# encoding: utf8
import os
import json
import datetime
import requests
import smtplib
import csv
import sys, getopt
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

FROM_ADDR = 'pd.system@bespinglobal.cn'
FROM_PASS = ''
TO_ADDR = 'cairong.li@bespinglobal.cn'
SMTP_SERVER = 'mail.bespinglobal.cn'
SMTP_PORT = 587

params = {
    "token": '',
    "since_date": '',
    "until_date": ''
}

token = ""
base_url = "https://git.opsnow.tech/api/v4"
cur_date = datetime.datetime.now()
#pre_date = (cur_date).strftime("%Y-%m-%d")
pre_date = "2019-07"
#since_date = (cur_date - datetime.timedelta(days=2)).strftime("%Y-%m-%d 22:00:00")
#until_date = (cur_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d 22:00:00")
#until_date = cur_date.strftime("%Y-%m-%d 22:00:00")
# since_date = "2019-08-08 00:00:00"
# until_date = "2019-08-15 00:00:00"
project_result = {}
#防重处理
all_commits={}

email_name={
    "long.liu@bespinglobal.cn":"刘龙",
    "zhiwu.ma@bespinglobal.cn":"马治武",
    "cairong.li@bespinglobal.cn":"李才荣",
    "haiyang.dai@bespinglobal.cn":"代海洋",
    "xin.rao@bespinglobal.cn":"饶鑫",
    "zhihao.lu@bespinglobal.cn":"鲁志豪",
    "shanshan.xu@bespinglobal.cn":"许姗姗",
    "yuan.yang@bespinglobal.cn":"杨原",
    "jianwei.xu@bespinglobal.cn":"徐建伟",
    "shuai.hu@bespinglobal.cn":"胡帅",
    "qiuyue.luo@bespinglobal.cn":"罗秋悦",
    "dong.li@bespinglobal.cn":"李东",
    "vwater.wang@bespinglobal.cn":"王永",
    "yewei.du@bespinglobal.cn":"杜业伟",
    "zhanjia.chen@bespinglobal.cn":"陈展佳",
    "xing.jin@bespinglobal.cn":"金星",
    "jiashu.du@bespinglobal.cn":"杜嘉澍",
    "xuliang.zhang@bespinglobal.cn":"张旭亮",
    "xiyue.huang@bespinglobal.cn":"黄希悦",
    "lifeng.weng@bespinglobal.cn":"翁励烽",
    "wei.zhang@bespinglobal.cn":"张炜",
    "yue.zheng@bespinglobal.cn":"郑岳",
    "zhiqiang.qian@bespinglobal.cn":"钱志强",
    "xiansheng.liu@bespinglobal.cn":"刘显胜",
    "huichen.yu@bespinglobal.cn":"余慧晨",
    "jun.ma@bespinglobal.cn":"马俊",
    "jin.yang@bespinglobal.cn":"杨锦",
    "congli.wang@bespinglobal.cn":"王聪丽",
    "xin.ping@bespinglobal.cn":"平鑫",
    "ying.xue@bespinglobal.cn":"薛莹",
    "jian.yu@bespinglobal.cn":"喻建",
    "yanfei.liu@bespinglobal.cn":"刘艳菲",
    "chengyao.su@bespingloal.cn":"苏成尧",
    "sun.zhang@bespinglobal.cn":"张笋",
    "haoran.li@bespinglobal.cn":"李浩然",
    "lan.liu@bespinglobal.cn":"刘兰",
    "zhiyong.xu@bespinglobal.cn":"徐志勇",
    "wyqbxzy@126.com":"徐志勇"
}

def get_data(url):
    print('token:', params)
    headers = {
        "PRIVATE-TOKEN": params['token']
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

# /projects/:id/repository/commits?ref_name=master&since=&until=
def get_commits(project_id, project_name, branch_name, group_name):
    url = "%s/projects/%s/repository/commits?per_page=2000&ref_name=%s&since=%s&until=%s&with_stats=yes" % (base_url, project_id, branch_name, params['since_date'], params['until_date'])
    rs = get_data(url)

    commit_details = []

    for commit in rs:
        commit_id = commit['id']
        if commit_id in all_commits:
            continue
        all_commits[commit_id] = commit
        stats = commit['stats']

        author_name = commit['author_name']
        commiter_email = commit['committer_email']
        if commiter_email in email_name:
            author_name = email_name[commiter_email]
        commit_details.append({
                'commit_id': commit_id,
                'name': commit['committer_name'], 
                'email': commit['committer_email'], 
                'author_name': author_name,
                'group': group_name,
                'project':project_name, 
                'branch': branch_name, 
                'additions': stats['additions'], 
                'deletions': stats['deletions'], 
                'total': stats['total'],
                'commit_count': 1
                })
    return commit_details

# /projects/:id/repository/branches/
def get_branches(project_id):
    url = "%s/projects/%s/repository/branches?per_page=2000" % (base_url, project_id)
    rs = get_data(url)

    result = []
    for branch in rs:
        result.append(branch['name'])
    return result

# /projects
def get_projects():
    url = "%s/projects?per_page=2000" % base_url
    rs = get_data(url)

    print(rs)

    projects = []

    full_paths = {}

    for project in rs:
        project_name = project['name']
        project_full_path = project['namespace']['full_path']
        full_paths[project_full_path] = {}
        if project_full_path.startswith('PD/Private2.0') or project_full_path.startswith('oc-si') or project_full_path.startswith('PD/Private'):
            print('开始获取项目:',project_full_path,'/',project_name,'分支')
            branches = get_branches(project['id'])
            print('获取项目:',project_full_path,'/',project_name,'分支结束，分支个数：',len(branches))
            p = {
                "id": project['id'],
                "name": project['name'],
                "path_with_namespace": project['path_with_namespace'],
                "ssh_url_to_repo": project['ssh_url_to_repo'],
                "http_url_to_repo": project['http_url_to_repo'],
                "namespace": project['namespace']['full_path'],
                "branches": branches
            }
            projects.append(p)
        else:
            print('项目:', project_name, '不进行统计, 跳过')

    # print(full_paths)
    return projects

def write_csv_obj(filename, headers, data_rows):
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        f_csv.writerows(data_rows)

def write_csv_dict(filename, headers, data_dict):
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()

        for k, v in data_dict.items():
            f_csv.writerow(v)
    
def usage():
    msg = "Usage: %s -t <token> -s <since_date> -u <until_date> [-h] or %s --token <token> --sincedate <since_date> --untildate <until_date> [--help]" % (sys.argv[0], sys.argv[0])
    print(msg)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "ht:s:u:", ["help", "token=", "sincedate=", "untildate="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    has_token = 0
    has_since_date = 0
    has_until_date = 0
    for opt, arg in opts:
        if opt in ('h', 'help'):
            usage()
            sys.exit()
        elif opt in ("-t", "--token"):
            params['token'] = arg
            has_token = 1
        elif opt in ("-s", "--sincedate"):
            params['since_date'] = arg
            has_since_date = 1
        elif opt in ("-u", "--untildate"):
            params['until_date'] = arg
            has_until_date = 1

    if has_token == 0 or has_since_date == 0 or has_until_date == 0:
        usage()
        sys.exit()

    print(params)
    stas()

def stas():
    projects = get_projects()
    print('获取所有项目及其分支结束，共有项目个数：', len(projects))

    project_headers = ["id","name","path_with_namespace","ssh_url_to_repo","http_url_to_repo","namespace","branches"]
    write_csv_obj('./projects.csv', project_headers, projects)

    print('1. 获取项目结束， 共有项目数量：', len(projects))

    return

    commits = []

    for p in projects:
        project_id = p['id']
        project_name = p['name']
        for branch_name in p['branches']:
            branch_commits = get_commits(project_id, project_name, branch_name, p['namespace'])
            print('3. 获取项目', p['namespace'], '/', project_name, ' 分支：', branch_name, '所有提交结束, len:', len(branch_commits))
            commits += branch_commits
            print('total commits len:', len(commits))

    print('commits len:', len(commits))
    return

    commit_details_headers = ['commit_id','name', 'email', 'author_name','group','project', 'branch', 'additions', 'deletions', 'total','commit_count']
    # 保存提交日志明细到commit_details.csv文件
    write_csv_obj('./commit_details.csv', commit_details_headers, commits)

    author_stats = {}

    print('4. 获取所有提交结束，开始进行统计')
    for commit in commits:
        author_name = commit['email']
        if author_name in author_stats:
            author_commit = author_stats[author_name]
            author_commit['additions'] += commit['additions']
            author_commit['deletions'] += commit['deletions']
            author_commit['total'] += commit['total']
            author_commit['commit_count'] += 1
        else:
            author_stats[author_name] = {
                'name': commit['name'], 
                'email': commit['email'], 
                'author_name': commit['author_name'],
                'group': commit['group'],
                'project':commit['project'],
                'additions': commit['additions'],
                'deletions': commit['deletions'],
                'total': commit['total'],
                'commit_count': commit['commit_count']
            }

    # print(author_stats)

    commit_stats_headers = ["group", "project", "email", "name", 'author_name', "additions", "deletions", "total", "commit_count"]
    write_csv_dict('./commit_stats.csv', commit_stats_headers, author_stats)
    # write_csv_file(author_stats)

    # for k, v in author_stats.items():
    #     print('%s , %s, %s, %s, %s, %s, %s, %s' % (v['group'], v['email'], v['name'], v['author_name'], v['additions'], v['deletions'], v['total'], v['commit_count']))

if __name__ == "__main__":
    main(sys.argv[1:])
    #print json.dumps(get_projects())
