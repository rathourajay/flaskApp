#include "ensiwcmem.h"
#include "ensiwcq.h"

int main(int argc, char* argv[])
{
  ENSIWCMem::unit_test();
  ENSIWCQ<int32_t>::unit_test();
}
