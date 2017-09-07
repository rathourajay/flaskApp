#include <Python.h>
#include <structmember.h>
#include <stdio.h>

#include "ensiwcworkload.h"

typedef struct
{
  PyObject_HEAD
  /* Type-specific fields go here. */
  ENSIWCWorkload* workload;
} ensiwc_WorkloadObject;

extern "C" {
static int
Workload_init(ensiwc_WorkloadObject *self, PyObject *args, PyObject *kwds)
{
  int id;
  int qsize;
  int memsize;

  static char *kwlist[] = {"id", "qsize", "memsize", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iii", kwlist, &id, &qsize, &memsize))
  {
    printf("Failed to parse arguments\n");
    fflush(stdout);
    PyErr_SetString(PyExc_RuntimeError, "Failed to parse ensiwc.Workload init arguments");
    return -1;
  }

  printf("Creating ENSIWCWorkload(%d, %d, %d)\n", id, qsize, memsize);
  fflush(stdout);
  self->workload = new ENSIWCWorkload(id, qsize, memsize);
  printf("Workload = %p\n", self->workload);
  fflush(stdout);

  if (!self->workload)
  {
    printf("Failed to create ENSIWCWorkload\n");
    fflush(stdout);
    PyErr_SetString(PyExc_RuntimeError, "Failed to create ENSIWCWorkload object");
    return -1;
  }
  printf("Starting ENSIWCWorkload object\n");
  fflush(stdout);
  self->workload->start();
  printf("Started ENSIWCWorkload object\n");
  fflush(stdout);

  return 0;
}

static void
Workload_dealloc(ensiwc_WorkloadObject* self)
{
  if (self->workload)
  {
    delete self->workload;
    self->workload = NULL;
  }
}

static PyObject *
Workload_recv(ensiwc_WorkloadObject* self)
{
  printf("Workload_recv\n");
  fflush(stdout);
  PyObject *py_string;
  ENSIWCMsg msg;
  while (true)
  {
    printf("Calling recv\n");
    fflush(stdout);
    if (self->workload->recv(msg))
    {
      printf("Received message, id = %d\n", msg.msg_id);
      fflush(stdout);
      if (msg.msg_id == MSG_EVENT)
      {
        printf("Converting data %p to Python string\n", self->workload->msg_data(msg));
        fflush(stdout);
        printf("Message = %.*s\n", (int)msg.length, self->workload->msg_data(msg));
        fflush(stdout);
        py_string = PyString_FromStringAndSize((const char*)self->workload->msg_data(msg), msg.length);
        printf("Converted text\n");
        fflush(stdout);
        self->workload->free(msg.data);
        printf("Freed data\n");
        fflush(stdout);
        break;
      }
      else if (msg.msg_id == MSG_WORKLOAD_TERM)
      {
        printf("Workload terminating\n");
        fflush(stdout);
        py_string = PyString_FromString("");
        break;
      }
    }
    else
    {
      printf("Error, recv returned nothing\n");
      fflush(stdout);
      py_string = PyString_FromString("");
      break;
    }
  }
  printf("Returning string\n");
  fflush(stdout);
  return py_string;
}

static PyObject *
Workload_send(ensiwc_WorkloadObject *self, PyObject *arg)
{
  printf("Workload_send (%p)\n", arg);
  fflush(stdout);
  int rc = 0;
  ENSIWCMsg msg;
  msg.msg_id = MSG_EVENT;
  msg.length = PyString_Size(arg);
  printf("Length of data = %d\n", (int)msg.length);
  fflush(stdout);
  msg.data = self->workload->alloc(msg.length);
  printf("Allocated data for message, handle = %d, address = %p\n", msg.data, self->workload->msg_data(msg));
  fflush(stdout);
  if (msg.data)
  {
    printf("Message = %s\n", PyString_AsString(arg));
    fflush(stdout);
    memcpy(self->workload->msg_data(msg), PyString_AsString(arg), msg.length);
    printf("Copied message\n");
    fflush(stdout);
    rc = self->workload->send(msg);
    printf("Sent message, rc = %d\n", rc);
    fflush(stdout);
  }
  //Py_DECREF(arg);
  return PyBool_FromLong(rc);
}

static PyMethodDef Workload_methods[] = {
  {"recv", (PyCFunction)Workload_recv, METH_NOARGS, "Receive inbound messages for workload"},
  {"send", (PyCFunction)Workload_send, METH_O, "Send outbound messages from workload"},
  {NULL}  /* Sentinel */
};

static PyTypeObject ensiwc_WorkloadType =
{
  PyObject_HEAD_INIT(NULL)
  0,                           /* ob_size*/
  "ensiwc.Workload",           /* tp_name*/
  sizeof(ensiwc_WorkloadObject), /* tp_basicsize*/
  0,                           /* tp_itemsize*/
  (destructor)Workload_dealloc,  /* tp_dealloc*/
  0,                           /* tp_print*/
  0,                           /* tp_getattr*/
  0,                           /* tp_setattr*/
  0,                           /* tp_compare*/
  0,                           /* tp_repr*/
  0,                           /* tp_as_number*/
  0,                           /* tp_as_sequence*/
  0,                           /* tp_as_mapping*/
  0,                           /* tp_hash */
  0,                           /* tp_call*/
  0,                           /* tp_str*/
  0,                           /* tp_getattro*/
  0,                           /* tp_setattro*/
  0,                           /* tp_as_buffer*/
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
  "Workload objects",          /* tp_doc */
  0,		               /* tp_traverse */
  0,		               /* tp_clear */
  0,		               /* tp_richcompare */
  0,		               /* tp_weaklistoffset */
  0,		               /* tp_iter */
  0,		               /* tp_iternext */
  Workload_methods,            /* tp_methods */
  0,                           /* tp_members */
  0,                           /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)Workload_init,     /* tp_init */
  0,                           /* tp_alloc */
  0,                           /* tp_new */
};

static PyMethodDef ensiwc_methods[] = {
  {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initensiwc(void)
{
  PyObject* m;

  ensiwc_WorkloadType.tp_new = PyType_GenericNew;
  if (PyType_Ready(&ensiwc_WorkloadType) < 0)
      return;

  m = Py_InitModule3("ensiwc", ensiwc_methods,
                     "ENS Inter-workload communications module.");

  Py_INCREF(&ensiwc_WorkloadType);
  PyModule_AddObject(m, "Workload", (PyObject *)&ensiwc_WorkloadType);
}


}
