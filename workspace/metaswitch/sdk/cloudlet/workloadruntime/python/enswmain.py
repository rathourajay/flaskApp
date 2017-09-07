import sys
from enswr import ENSWorkloadRuntime

if len(sys.argv) == 1:
    print("Usage: %s <config>" % sys.argv[0])
    sys.exit(1)

ert = ENSWorkloadRuntime(sys.argv[1])
ert.run()
sys.exit(0)
