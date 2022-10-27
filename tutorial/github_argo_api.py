from github import Github, InputGitAuthor
import os
from pprint import pprint
from flask import Flask
from flask import request
import json
import yaml
from yaml import load, dump

"""
# Install GH CLI:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
&& sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y

# Upgrade GH CLI:
sudo apt update
sudo apt install gh

# Manually access Github REST APIs
1/ curl -u USERNAME:TOKEN https://api.github.com/user
2/ curl \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/tqhuy812/argocd-helloworld/branches

# REFERENCES
https://martinheinz.dev/blog/25
https://pygithub.readthedocs.io/en/latest/examples/Repository.html
"""


BL_ENGINE_IP = os.getenv("BL_ENGINE_IP", "0.0.0.0")
BL_ENGINE_PORT = int(os.getenv("BL_ENGINE_PORT", 30316))
app = Flask(__name__)
MASTER_BRANCH = "main"
GITHUB_ARGOCD_TOKEN = "GITHUB_ARGOCD_TOKEN"
REPO = "tqhuy812/argocd-helloworld"

token = os.getenv(GITHUB_ARGOCD_TOKEN, '')
# print(token)
g = Github(token)
repo = g.get_repo(REPO)
# issues = repo.get_issues(state="open")
# pprint(issues.get_page(0))

def push_to_repo(path, message, content, branch, update=False):
    author = InputGitAuthor(
        "Huy Tran",
        "tqhuy812@gmail.com"
    )
    # source = repo.get_branch("master")
    # repo.create_git_ref(ref=f"refs/heads/{branch}", sha=source.commit.sha)  # Create new branch from master
    if update:  # If file already exists, update it
        contents = repo.get_contents(path, ref=branch)  # Retrieve old file to get its SHA and path
        repo.update_file(contents.path, message, content, contents.sha, branch=branch, author=author)  # Add, commit and push branch
    else:  # If file doesn't exist, create it
        repo.create_file(path, message, content, branch=branch, author=author)  # Add, commit and push branch


'''
printf '{"version":"2.2.1"}'| http  --follow --timeout 3600 POST '127.0.0.1:30316/change_sdnc_version' Content-Type:'application/json'
'''
@app.route('/change_sdnc_version', methods=['POST'])
def transform():
    required_sdnc_version = request.get_json(force=True)['version'] 
    current_sdnc_version = "0.0"
    depl_file = repo.get_contents("onos/k8s-depl-onos.yaml", ref=MASTER_BRANCH)
    contents_depl_file = depl_file.decoded_content.decode("utf-8")
    yaml_depl = yaml.safe_load(contents_depl_file)
    container_list = yaml_depl['spec']['template']['spec']['containers']
    for container in container_list:
        if container['name'] == "onos-demo":
            image_name = container['image'].split(':')[0]
            current_sdnc_version = container['image'].split(':')[1]
            if current_sdnc_version != required_sdnc_version: 
                container['image'] = image_name + ":" + required_sdnc_version
            else:
                return yaml.dump(yaml_depl), 304 # Not Modified
    push_to_repo(depl_file.path, "Update k8s-depl-onos.yaml", yaml.dump(yaml_depl), MASTER_BRANCH, update=True)
    return yaml.dump(yaml_depl), 200




if __name__ == '__main__':


    app.run(host=BL_ENGINE_IP,port=BL_ENGINE_PORT,debug=True,use_reloader=True)
