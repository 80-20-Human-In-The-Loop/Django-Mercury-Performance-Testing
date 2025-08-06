/*
 * Python C API wrapper for Django Mercury Performance Monitor
 * Provides real-time performance monitoring with minimal overhead
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "common.h"  /* Includes windows_compat.h for cross-platform time functions */
#include <string.h>

/* Performance Monitor Structure */
typedef struct {
    PyObject_HEAD
    double start_time;
    double response_time_ms;
    int query_count;
    int cache_hits;
    int cache_misses;
    int monitoring;
    PyObject* queries;  /* List of query dicts */
} PerformanceMonitor;

/* Helper: Get current time in seconds */
static double get_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

/* Destructor */
static void
PerformanceMonitor_dealloc(PerformanceMonitor *self)
{
    Py_XDECREF(self->queries);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/* Constructor */
static PyObject *
PerformanceMonitor_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PerformanceMonitor *self;
    self = (PerformanceMonitor *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->start_time = 0.0;
        self->response_time_ms = 0.0;
        self->query_count = 0;
        self->cache_hits = 0;
        self->cache_misses = 0;
        self->monitoring = 0;
        self->queries = PyList_New(0);
        if (self->queries == NULL) {
            Py_DECREF(self);
            return NULL;
        }
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
    if (!self->monitoring) {
        self->monitoring = 1;
        self->start_time = get_time();
        /* Reset metrics */
        self->response_time_ms = 0.0;
        self->query_count = 0;
        self->cache_hits = 0;
        self->cache_misses = 0;
        Py_CLEAR(self->queries);
        self->queries = PyList_New(0);
    }
    Py_RETURN_NONE;
}

/* Stop monitoring method */
static PyObject *
PerformanceMonitor_stop_monitoring(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    if (self->monitoring) {
        double end_time = get_time();
        self->response_time_ms = (end_time - self->start_time) * 1000.0;
        self->monitoring = 0;
    }
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
    
    /* Create query dict */
    PyObject *query_dict = PyDict_New();
    if (query_dict) {
        PyDict_SetItemString(query_dict, "sql", PyUnicode_FromString(sql));
        PyDict_SetItemString(query_dict, "duration", PyFloat_FromDouble(duration));
        PyList_Append(self->queries, query_dict);
        Py_DECREF(query_dict);
    }
    
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
    
    PyDict_SetItemString(metrics, "response_time_ms", PyFloat_FromDouble(self->response_time_ms));
    PyDict_SetItemString(metrics, "query_count", PyLong_FromLong(self->query_count));
    PyDict_SetItemString(metrics, "cache_hits", PyLong_FromLong(self->cache_hits));
    PyDict_SetItemString(metrics, "cache_misses", PyLong_FromLong(self->cache_misses));
    PyDict_SetItemString(metrics, "implementation", PyUnicode_FromString("c_extension"));
    
    /* Calculate cache hit ratio if applicable */
    int total_cache = self->cache_hits + self->cache_misses;
    if (total_cache > 0) {
        double hit_ratio = (double)self->cache_hits / total_cache;
        PyDict_SetItemString(metrics, "cache_hit_ratio", PyFloat_FromDouble(hit_ratio));
    }
    
    return metrics;
}

/* Reset method */
static PyObject *
PerformanceMonitor_reset(PerformanceMonitor *self, PyObject *Py_UNUSED(ignored))
{
    self->start_time = 0.0;
    self->response_time_ms = 0.0;
    self->query_count = 0;
    self->cache_hits = 0;
    self->cache_misses = 0;
    self->monitoring = 0;
    Py_CLEAR(self->queries);
    self->queries = PyList_New(0);
    
    Py_RETURN_NONE;
}

/* Metrics property getter */
static PyObject *
PerformanceMonitor_get_metrics_property(PerformanceMonitor *self, void *closure)
{
    /* Return a simple metrics object/dict for compatibility */
    PyObject *metrics = PyDict_New();
    if (metrics == NULL) {
        return NULL;
    }
    
    PyDict_SetItemString(metrics, "response_time_ms", PyFloat_FromDouble(self->response_time_ms));
    PyDict_SetItemString(metrics, "query_count", PyLong_FromLong(self->query_count));
    PyDict_SetItemString(metrics, "cache_hits", PyLong_FromLong(self->cache_hits));
    PyDict_SetItemString(metrics, "cache_misses", PyLong_FromLong(self->cache_misses));
    
    return metrics;
}

/* Method definitions */
static PyMethodDef PerformanceMonitor_methods[] = {
    {"start_monitoring", (PyCFunction) PerformanceMonitor_start_monitoring, METH_NOARGS,
     "Start monitoring performance"},
    {"stop_monitoring", (PyCFunction) PerformanceMonitor_stop_monitoring, METH_NOARGS,
     "Stop monitoring and calculate metrics"},
    {"track_query", (PyCFunction) PerformanceMonitor_track_query, METH_VARARGS,
     "Track a database query"},
    {"track_cache", (PyCFunction) PerformanceMonitor_track_cache, METH_VARARGS,
     "Track a cache hit or miss"},
    {"get_metrics", (PyCFunction) PerformanceMonitor_get_metrics, METH_NOARGS,
     "Get collected metrics"},
    {"reset", (PyCFunction) PerformanceMonitor_reset, METH_NOARGS,
     "Reset all metrics"},
    {NULL}  /* Sentinel */
};

/* Properties */
static PyGetSetDef PerformanceMonitor_getsetters[] = {
    {"metrics", (getter)PerformanceMonitor_get_metrics_property, NULL,
     "Access to metrics", NULL},
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
    .tp_getset = PerformanceMonitor_getsetters,
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