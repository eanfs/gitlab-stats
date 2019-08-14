# encoding: utf8
import os
import json
import datetime
import requests
import smtplib
import csv
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

FROM_ADDR = 'pd.system@bespinglobal.cn'
FROM_PASS = ''
TO_ADDR = 'cairong.li@bespinglobal.cn'
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
since_date = "2019-08-10 00:00:00"
until_date = "2019-08-15 00:00:00"
project_result = {}
#防重处理
all_commits={}

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

# /projects/:id/repository/commits?ref_name=master&since=&until=
def get_commits(project_id, project_name, branch_name, group_name):
    url = "%s/projects/%s/repository/commits?per_page=2000&ref_name=%s&since=%s&until=%s&with_stats=yes" % (base_url, project_id, branch_name, since_date, until_date)
    rs = get_data(url)

    commit_details = []

    for commit in rs:
        commit_id = commit['id']
        if commit_id in all_commits:
            continue
        all_commits[commit_id] = commit
        stats = commit['stats']
        commit_details.append({
                'commit_id': commit_id,
                'name': commit['committer_name'], 
                'email': commit['committer_email'], 
                'author_name': commit['author_name'],
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
        branch_name = branch['name']
        result.append(branch_name)
    return result

# /projects
def get_projects():
    url = "%s/projects?per_page=2000" % base_url
    rs = get_data(url)

    projects = []

    namespaces = {}

    count = 0
    for project in rs:
        p = {
            "id": project['id'],
            "name": project['name'],
            "path_with_namespace": project['path_with_namespace'],
            "ssh_url_to_repo": project['ssh_url_to_repo'],
            "http_url_to_repo": project['http_url_to_repo'],
            "namespace": project['namespace']['full_path'],
            "branches": []
        }
        if p['namespace'].startswith('PD/Private2.0') or p['namespace'].startswith('oc-si'):
            projects.append(p)
        namespaces[p['namespace']] = {}

    # result = {"BP-CMP": [], "BP-BILLING": [], "BP-MONITOR": [], "BP-AUTOMATE": [], "BP-FRONT-END": [], "BP-CMDB": [], "BP-TICKET": [], "BP-IAM": [], "BP-NOTIFIER": []}
    # for p in rs:
    #     for k in result.keys():
    #         if p['namespace']['full_path'].startswith('PD/Private2.0/%s' % k):
    #             result[k].append({"id": p['id'], "name": p['name'], "ssh_url_to_repo": p['ssh_url_to_repo'], "branches": []})
    #             break
    print(namespaces)
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
    

def main():
    projects = get_projects()

    project_headers = ["id",
            "name",
            "path_with_namespace",
            "ssh_url_to_repo",
            "http_url_to_repo",
            "namespace",
            "branches"]
    write_csv_obj('./projects.csv', project_headers, projects)

    print('1. 获取项目结束， 共有项目数量：', len(projects))

    commits = []

    for p in projects:
        project_id = p['id']
        project_name = p['name']
        branches = get_branches(project_id)
        p['branches'] = branches
        print('2. 获取项目', project_name, '分支结束')
        for b in branches:
            branch_commits = get_commits(project_id, project_name, b, p['namespace'])
            print('3. 获取项目', p['namespace'], '/', project_name, ' 分支：', b, '所有提交结束, len:', len(branch_commits))
            commits += branch_commits
            print('total commits len:', len(commits))

    # for k, v in projects.items():
    #     for p in v:
    #         project_id = p['id']
    #         project_name = p['name']
    #         branches = get_branches(project_id)
    #         p['branches'] = branches
    #         print('2. 获取项目', project_name, '分支结束')

    #         for b in branches:
    #             branch_commits = get_commits(project_id, project_name, b, k)
    #             print('3. 获取项目', project_name, ' 分支：', b, '所有提交结束, len:', len(branch_commits))
    #             commits += branch_commits
    #             print('total commits len:', len(commits))

    print('commits len:', len(commits))

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
    main()
    #print json.dumps(get_projects())
