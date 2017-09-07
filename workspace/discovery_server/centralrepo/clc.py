from flask import Flask, request, Response
import requests
import json
import os
import httplib
import threading

cld_id = 'ens.aws-us-west.edgenet.cloud'
MEC_CLC_PORT = 0xed24
DOCKER_GLOBAL_REG_UNAME = 'testuser'
DOCKER_GLOBAL_REG_PASS = 'testpassword'
DOCKER_LOCAL_REG_UNAME = 'testuser'
DOCKER_LOCAL_REG_PASS = 'testpassword'
LOCAL_REG_URL = '10.206.86.6:20000'
GLOBAL_REG_URL = '10.206.86.27:33000'

clc = Flask(__name__)


@clc.route('/api/v1.0/clc/notify', methods=['POST'])
def update_docker_registry():
    image_tag = request.json['tag']
    docker_image_name = request.json['repository']
#     GLOBAL_REG_URL = request.args.get('url')
    image_catalog_url = "http://%s:%s@%s/v2/_catalog" % (
        DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)
    tag_list_url = "http://%s:%s@%s/v2/%s/tags/list" % (
        DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL, docker_image_name)

    ### Getting list of images in local registry ###
    image_catalog_dict = json.loads(requests.get(image_catalog_url).content)

    ### Getting tag list of image in local registry ###
    image_tag_dict = json.loads(requests.get(tag_list_url).content)

    ### Checking if the new image pushed in global registry is present in local registry ###
    # If it is not present in local registry then pull it from global and push
    # it is in local registry ###
    if (docker_image_name not in image_catalog_dict['repositories']) or \
            (docker_image_name in image_catalog_dict['repositories'] and image_tag not in image_tag_dict['tags']):

        ### Commands for PULLING image from global registry ###
        login_cmd_global_reg = 'sudo docker login -u %s -p %s -e "\n" %s' % (
            DOCKER_GLOBAL_REG_UNAME, DOCKER_GLOBAL_REG_PASS, GLOBAL_REG_URL)

        image_tag_global = GLOBAL_REG_URL + \
            '/' + docker_image_name + ':' + image_tag

        pull_cmd = 'sudo docker pull %s' % (image_tag_global)

        logout_cmd_global_reg = "sudo docker logout %s" % (GLOBAL_REG_URL)

        ### Commands for PUSHING image to locaal registry ###
        login_cmd_local_reg = 'sudo docker login -u %s -p %s -e "\n" %s' % (
            DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)
        create_tag_cmd = "sudo docker tag %s %s/%s:%s" % (
            image_tag_global, LOCAL_REG_URL, docker_image_name, image_tag)

        push_cmd = "sudo docker push %s/%s:%s" % (
            LOCAL_REG_URL, docker_image_name, image_tag)

        logout_cmd_local_reg = "sudo docker logout %s" % (LOCAL_REG_URL)

        ### Pulling image from global registry ###
        print "Pulling image from global registry ========="
        os.system(
            login_cmd_global_reg + ";" + pull_cmd + ";" + logout_cmd_global_reg)
        ### Pushing Image ###
        print "Pushing Image with tag %s" % image_tag
        os.system(login_cmd_local_reg + ";" + create_tag_cmd +
                  ";" + push_cmd + ";" + logout_cmd_local_reg)
        return Response(status=httplib.OK)
    else:
        print "Image [", docker_image_name, "/", image_tag, "] already present in local registry"
        return Response(response="%s:ALREADY_EXISTS" % docker_image_name, status=httplib.CONFLICT)


@clc.route('/api/v1.0/clc/docker_images', methods=['GET'])
def list_docker_images():
    #list_images = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/_catalog'
    #list_tags = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/%s/tags/list"' %repo_name
    list_images_url = "http://%s:%s@%s/v2/_catalog" % (
        DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)

    image_dict = requests.get(list_images_url).content

    return image_dict


def heartbeat():
    #     data = {'clc_id': cld_id}
    print cld_id
    resp = requests.put(
        "http://localhost:60677/api/v1.0/discover/heartbeat/%s" % cld_id)
    print resp, " ", resp.content
    threading.Timer(10, heartbeat).start()

if __name__ == '__main__':
    heartbeat()
    clc.run(host="0.0.0.0", port=MEC_CLC_PORT)  # , debug=True)
