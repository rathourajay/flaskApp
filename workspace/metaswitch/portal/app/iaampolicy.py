import dns.resolver
import subprocess
import json

class Manager:
    def __init__(self, policy_file):
        self.file = policy_file

        with open(self.file) as policy:
            print("Loading application policy database")
            self.policy = json.load(policy)

    def update_app(self, name, enabled, placement):
        app_policy = self.policy["applications"][name]
        if enabled:
            app_policy = {"enabled": "Y", "client-regions": ["NA", "EU"]}
            if placement == "low-latency":
                app_policy["low-latency"] = "Y"
            else:
                app_policy["low-latency"] = "N"
        else:
            app_policy = {"enabled": "N"}
        self.policy["applications"][name] = app_policy

        self.push_policy()

    def push_policy(self):
        with open(self.file, 'w') as outfile:
            json.dump(self.policy, outfile)
        outfile.close()

        iaam = dns.resolver.query('iaam.edgenet.cloud', 'A')
        print("IAAM locations = %s" % ','.join([str(c) for c in iaam]))
        for c in iaam:
            cmd = ["scp", "-B", "-i", "/home/ubuntu/.ssh/ens.pem", self.file, "ubuntu@%s:ens/policy" % str(c)]
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            print("Pushed policy to %s" % str(c))








