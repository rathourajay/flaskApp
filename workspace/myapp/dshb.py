from flask import Flask
import time
from flask import Flask, request, Response, jsonify

app = Flask(__name__)


@app.route("/api/call", methods=["GET"])
def comparetime():
    timer = time.clock()
    print "inside method"
    status = request.args.get('status')
    import pdb
    pdb.set_trace()
    if ((time.time() - timer) < 30):
        timer = time.clock()
        print "inside if"
        return "cloudlet is up"
    else:
        return "fail"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6005)
