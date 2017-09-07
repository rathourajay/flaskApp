// Event handler function for simple latency test responder.

#include <stdint.h>

extern "C" {
uint8_t* event_handler(uint8_t* event)
{
  return event;
}
}


