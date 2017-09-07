from flask import Flask, request,  Response


MEC_CMS_PORT = 0xc350

cms = Flask(__name__)


@cms.route('/api/v1.0/llo/cms/events', methods=['POST', 'PUT'])
#@cms.route('/events',methods=['POST','GET'])
def cloudlet_events():
    cloudlet = request.args.get('cloudlet')
    status = request.args.get('status')
#     import pdb
#     pdb.set_trace()
    print "cloudlet: ", cloudlet, "status: ", status
    return Response(response="EVENT_LISTENED")


if __name__ == '__main__':
    cms.run(host="0.0.0.0", port=MEC_CMS_PORT, debug=True)
