# gitlab代码统计

## 获取token

1. 登录gitlab, 使用一个权限大的账号；
2. 点击右上角->Settings
3. 左侧选择`AccessToken`, 输入token名称， 选择权限范围，这里我们勾选api:

    ![access-token](/imgs/gitlab_settings_token.jpg)
4. 点击`Create personal access token` 按钮, 复制下来生成的个人账号访问token

    ![access-token2](/imgs/gitlab_settings_token2.jpg)

## 统计代码量

`gitlab_commit_stats.py`脚本为代码量统计脚本，使用语法：

```bash
$ python3 gitlab_commit_stats.py
Usage: python gitlab_commit_stats.py -t <token> -s <since_date> -u <until_date> -a <api_url> [-h] 
 or python gitlab_commit_stats.py --token <token> --sincedate <since_date> --untildate <until_date> --apiurl <api_url> [--help]
```

##### 参数

* `-t <token>`: 指定token
* `-s <since_date>`: 指定统计的起始时间， eg. 2019-09-01 00:00:00
* `-u <until_date>`: 指定统计的截至时间, eg. 2019-09-30 23:59:59
* `-a <api_url>`: 指定gitlab api地址, eg. https://gitlab.com/api/v4 
* `-h help`: 帮助说明