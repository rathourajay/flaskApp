import subprocess
import os
import json
import requests
tag = '123'
repo_name = 'ens/latencyresponder'
#list_images = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/_catalog'
#list_tags = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/%s/tags/list"' %repo_name
list_tags = "http://testuser:testpassword@10.206.86.6:20000/v2/%s/tags/list" % repo_name
#image_tag_dict = os.system(list_tags)
image_tag_dict = requests.get(list_tags).content
image_tag_dict = json.loads(image_tag_dict)
import pdb
pdb.set_trace()
if tag not in image_tag_dict['tags']:
    tag = 'latest'
    repo = "10.206.86.6:20000/%s:%s" % (repo_name, tag)
    print "Pulling image ========="
    #pull_cmd = 'sudo docker login -u testuser -p testpassword -e "\n" 10.206.86.6:20000;sudo docker pull ' + str(repo)
    #p1 = os.system(pull_cmd)

    tag = 123
    create_tag = "sudo docker tag ubuntu 10.206.86.6:20000/%s:%s" % (
        repo_name, tag)
    os.system(create_tag)
    print "Pushing Image with tag %s" % tag
    push_cmd = "sudo docker push 10.206.86.6:20000/%s:%s" % (repo_name, tag)
    os.system(push_cmd)
    logout_cmd = "sudo docker logout 10.206.86.6:20000"
    os.system(logout_cmd)
else:
    print "Image [", repo_name, "/", tag, "] presents in registry already"
