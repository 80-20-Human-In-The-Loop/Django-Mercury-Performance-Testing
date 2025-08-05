/*
 * Python C API wrapper for Django Mercury C extensions
 * This provides the Python interface to our C performance monitoring
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "common.h"  /* This includes windows_compat.h which has gettimeofday for Windows */
#include <time.h>
#ifndef _WIN32
    #include <sys/time.h>
#endif

/* Performance Monitor Structure */
typedef struct {
    PyObject_HEAD
    struct timeval start_time;
    struct timeval end_time;
    double response_time_ms;
    int query_count;
    int cache_hits;
    int cache_misses;
    int is_monitoring;
} PerformanceMonitor;

/* Destructor */
static void
PerformanceMonitor_dealloc(PerformanceMonitor *self)
{
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/* Constructor */
static PyObject *
PerformanceMonitor_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PerformanceMonitor *self;
    self = (PerformanceMonitor *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->response_time_ms = 0.0;
        self->query_count = 0;
        self->cache_hits = 0;
        self->cache_misses = 0;
        self->is_monitoring = 0;
    }
    return (PyObject *) self;
}

/* Initialize */
static int
PerformanceMonitor_init(PerformanceMonitor *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

/* Start monitoring method */
static PyObject *
PerformanceMonitor_start_monitoring(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    if (self->is_monitoring) {
        Py_RETURN_NONE;
    }
    
    gettimeofday(&self->start_time, NULL);
    self->is_monitoring = 1;
    self->query_count = 0;
    
    Py_RETURN_NONE;
}

/* Stop monitoring method */
static PyObject *
PerformanceMonitor_stop_monitoring(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    if (!self->is_monitoring) {
        Py_RETURN_NONE;
    }
    
    gettimeofday(&self->end_time, NULL);
    
    /* Calculate response time in milliseconds */
    double elapsed = (self->end_time.tv_sec - self->start_time.tv_sec) * 1000.0;
    elapsed += (self->end_time.tv_usec - self->start_time.tv_usec) / 1000.0;
    
    self->response_time_ms = elapsed;
    self->is_monitoring = 0;
    
    Py_RETURN_NONE;
}

/* Track query method */
static PyObject *
PerformanceMonitor_track_query(PerformanceMonitor *self, PyObject *args)
{
    const char *sql;
    double duration = 0.0;
    
    if (!PyArg_ParseTuple(args, "s|d", &sql, &duration)) {
        return NULL;
    }
    
    self->query_count++;
    
    Py_RETURN_NONE;
}

/* Track cache method */
static PyObject *
PerformanceMonitor_track_cache(PerformanceMonitor *self, PyObject *args)
{
    int hit;
    
    if (!PyArg_ParseTuple(args, "p", &hit)) {
        return NULL;
    }
    
    if (hit) {
        self->cache_hits++;
    } else {
        self->cache_misses++;
    }
    
    Py_RETURN_NONE;
}

/* Get metrics method */
static PyObject *
PerformanceMonitor_get_metrics(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    PyObject *metrics = PyDict_New();
    if (metrics == NULL) {
        return NULL;
    }
    
    PyDict_SetItemString(metrics, "response_time_ms", 
                        PyFloat_FromDouble(self->response_time_ms));
    PyDict_SetItemString(metrics, "query_count", 
                        PyLong_FromLong(self->query_count));
    PyDict_SetItemString(metrics, "cache_hits", 
                        PyLong_FromLong(self->cache_hits));
    PyDict_SetItemString(metrics, "cache_misses", 
                        PyLong_FromLong(self->cache_misses));
    PyDict_SetItemString(metrics, "implementation", 
                        PyUnicode_FromString("c_extension"));
    
    return metrics;
}

/* Reset method */
static PyObject *
PerformanceMonitor_reset(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    self->response_time_ms = 0.0;
    self->query_count = 0;
    self->cache_hits = 0;
    self->cache_misses = 0;
    self->is_monitoring = 0;
    
    Py_RETURN_NONE;
}

/* Method definitions */
static PyMethodDef PerformanceMonitor_methods[] = {
    {"start_monitoring", (PyCFunction) PerformanceMonitor_start_monitoring, METH_NOARGS,
     "Start performance monitoring"},
    {"stop_monitoring", (PyCFunction) PerformanceMonitor_stop_monitoring, METH_NOARGS,
     "Stop performance monitoring"},
    {"track_query", (PyCFunction) PerformanceMonitor_track_query, METH_VARARGS,
     "Track a database query"},
    {"track_cache", (PyCFunction) PerformanceMonitor_track_cache, METH_VARARGS,
     "Track cache hit or miss"},
    {"get_metrics", (PyCFunction) PerformanceMonitor_get_metrics, METH_NOARGS,
     "Get collected metrics"},
    {"reset", (PyCFunction) PerformanceMonitor_reset, METH_NOARGS,
     "Reset all metrics"},
    {NULL}  /* Sentinel */
};

/* Type definition */
static PyTypeObject PerformanceMonitorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "django_mercury._c_performance.PerformanceMonitor",
    .tp_doc = "C-based performance monitor for Django Mercury",
    .tp_basicsize = sizeof(PerformanceMonitor),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = PerformanceMonitor_new,
    .tp_init = (initproc) PerformanceMonitor_init,
    .tp_dealloc = (destructor) PerformanceMonitor_dealloc,
    .tp_methods = PerformanceMonitor_methods,
};

/* Module definition */
static PyModuleDef performancemodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_c_performance",
    .m_doc = "C extension for Django Mercury performance monitoring",
    .m_size = -1,
};

/* Module initialization */
PyMODINIT_FUNC
PyInit__c_performance(void)
{
    PyObject *m;
    
    if (PyType_Ready(&PerformanceMonitorType) < 0)
        return NULL;
    
    m = PyModule_Create(&performancemodule);
    if (m == NULL)
        return NULL;
    
    Py_INCREF(&PerformanceMonitorType);
    if (PyModule_AddObject(m, "PerformanceMonitor", (PyObject *) &PerformanceMonitorType) < 0) {
        Py_DECREF(&PerformanceMonitorType);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}