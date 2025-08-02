/*
 * Python C API wrapper for Django Mercury Metrics Engine
 * Provides statistical analysis and metrics aggregation
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <string.h>

/* Metrics Engine Structure */
typedef struct {
    PyObject_HEAD
    PyObject *metrics_list;  /* List of collected metrics */
    double total_response_time;
    int total_queries;
    int total_cache_hits;
    int total_cache_misses;
} MetricsEngine;

/* Destructor */
static void
MetricsEngine_dealloc(MetricsEngine *self)
{
    Py_XDECREF(self->metrics_list);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/* Constructor */
static PyObject *
MetricsEngine_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    MetricsEngine *self;
    self = (MetricsEngine *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->metrics_list = PyList_New(0);
        if (self->metrics_list == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->total_response_time = 0.0;
        self->total_queries = 0;
        self->total_cache_hits = 0;
        self->total_cache_misses = 0;
    }
    return (PyObject *) self;
}

/* Initialize */
static int
MetricsEngine_init(MetricsEngine *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

/* Add metrics method */
static PyObject *
MetricsEngine_add_metrics(MetricsEngine *self, PyObject *args)
{
    PyObject *metrics;
    
    if (!PyArg_ParseTuple(args, "O", &metrics)) {
        return NULL;
    }
    
    if (!PyDict_Check(metrics)) {
        PyErr_SetString(PyExc_TypeError, "metrics must be a dictionary");
        return NULL;
    }
    
    /* Extract and accumulate metrics */
    PyObject *response_time = PyDict_GetItemString(metrics, "response_time_ms");
    if (response_time && PyFloat_Check(response_time)) {
        self->total_response_time += PyFloat_AsDouble(response_time);
    }
    
    PyObject *query_count = PyDict_GetItemString(metrics, "query_count");
    if (query_count && PyLong_Check(query_count)) {
        self->total_queries += PyLong_AsLong(query_count);
    }
    
    /* Store the metrics */
    PyList_Append(self->metrics_list, metrics);
    
    Py_RETURN_NONE;
}

/* Calculate statistics method */
static PyObject *
MetricsEngine_calculate_statistics(MetricsEngine *self, PyObject *Py_UNUSED(ignored))
{
    PyObject *stats = PyDict_New();
    if (stats == NULL) {
        return NULL;
    }
    
    Py_ssize_t count = PyList_Size(self->metrics_list);
    
    if (count == 0) {
        PyDict_SetItemString(stats, "count", PyLong_FromLong(0));
        PyDict_SetItemString(stats, "mean", PyFloat_FromDouble(0.0));
        PyDict_SetItemString(stats, "min", PyFloat_FromDouble(0.0));
        PyDict_SetItemString(stats, "max", PyFloat_FromDouble(0.0));
        PyDict_SetItemString(stats, "std_dev", PyFloat_FromDouble(0.0));
        PyDict_SetItemString(stats, "implementation", PyUnicode_FromString("c_extension"));
        return stats;
    }
    
    /* Calculate statistics */
    double mean = self->total_response_time / count;
    double min_val = INFINITY;
    double max_val = -INFINITY;
    double sum_sq_diff = 0.0;
    
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *metric = PyList_GetItem(self->metrics_list, i);
        PyObject *rt = PyDict_GetItemString(metric, "response_time_ms");
        if (rt && PyFloat_Check(rt)) {
            double val = PyFloat_AsDouble(rt);
            if (val < min_val) min_val = val;
            if (val > max_val) max_val = val;
            double diff = val - mean;
            sum_sq_diff += diff * diff;
        }
    }
    
    double std_dev = sqrt(sum_sq_diff / count);
    
    PyDict_SetItemString(stats, "count", PyLong_FromSsize_t(count));
    PyDict_SetItemString(stats, "mean", PyFloat_FromDouble(mean));
    PyDict_SetItemString(stats, "min", PyFloat_FromDouble(min_val));
    PyDict_SetItemString(stats, "max", PyFloat_FromDouble(max_val));
    PyDict_SetItemString(stats, "std_dev", PyFloat_FromDouble(std_dev));
    PyDict_SetItemString(stats, "total_queries", PyLong_FromLong(self->total_queries));
    PyDict_SetItemString(stats, "implementation", PyUnicode_FromString("c_extension"));
    
    return stats;
}

/* Detect N+1 queries method */
static PyObject *
MetricsEngine_detect_n_plus_one(MetricsEngine *self, PyObject *args)
{
    PyObject *queries;
    
    if (!PyArg_ParseTuple(args, "O", &queries)) {
        return NULL;
    }
    
    if (!PyList_Check(queries)) {
        PyErr_SetString(PyExc_TypeError, "queries must be a list");
        return NULL;
    }
    
    PyObject *result = PyDict_New();
    if (result == NULL) {
        return NULL;
    }
    
    /* Simple N+1 detection based on query patterns */
    Py_ssize_t query_count = PyList_Size(queries);
    int similar_queries = 0;
    
    if (query_count > 1) {
        /* Check for similar query patterns */
        for (Py_ssize_t i = 0; i < query_count - 1; i++) {
            PyObject *q1 = PyList_GetItem(queries, i);
            PyObject *q2 = PyList_GetItem(queries, i + 1);
            
            if (PyDict_Check(q1) && PyDict_Check(q2)) {
                PyObject *sql1 = PyDict_GetItemString(q1, "sql");
                PyObject *sql2 = PyDict_GetItemString(q2, "sql");
                
                if (sql1 && sql2 && PyUnicode_Check(sql1) && PyUnicode_Check(sql2)) {
                    /* Simple check: if queries start with same pattern */
                    const char *s1 = PyUnicode_AsUTF8(sql1);
                    const char *s2 = PyUnicode_AsUTF8(sql2);
                    
                    if (s1 && s2 && strncmp(s1, s2, 50) == 0) {
                        similar_queries++;
                    }
                }
            }
        }
    }
    
    int detected = (similar_queries > 3);  /* Threshold for N+1 detection */
    
    PyDict_SetItemString(result, "detected", PyBool_FromLong(detected));
    PyDict_SetItemString(result, "query_count", PyLong_FromSsize_t(query_count));
    PyDict_SetItemString(result, "similar_queries", PyLong_FromLong(similar_queries));
    PyDict_SetItemString(result, "implementation", PyUnicode_FromString("c_extension"));
    
    return result;
}

/* Method definitions */
static PyMethodDef MetricsEngine_methods[] = {
    {"add_metrics", (PyCFunction) MetricsEngine_add_metrics, METH_VARARGS,
     "Add metrics to the engine"},
    {"calculate_statistics", (PyCFunction) MetricsEngine_calculate_statistics, METH_NOARGS,
     "Calculate statistics from collected metrics"},
    {"detect_n_plus_one", (PyCFunction) MetricsEngine_detect_n_plus_one, METH_VARARGS,
     "Detect N+1 query patterns"},
    {NULL}  /* Sentinel */
};

/* Type definition */
static PyTypeObject MetricsEngineType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "django_mercury._c_metrics.MetricsEngine",
    .tp_doc = "C-based metrics engine for Django Mercury",
    .tp_basicsize = sizeof(MetricsEngine),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = MetricsEngine_new,
    .tp_init = (initproc) MetricsEngine_init,
    .tp_dealloc = (destructor) MetricsEngine_dealloc,
    .tp_methods = MetricsEngine_methods,
};

/* Module definition */
static PyModuleDef metricsmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_c_metrics",
    .m_doc = "C extension for Django Mercury metrics engine",
    .m_size = -1,
};

/* Module initialization */
PyMODINIT_FUNC
PyInit__c_metrics(void)
{
    PyObject *m;
    
    if (PyType_Ready(&MetricsEngineType) < 0)
        return NULL;
    
    m = PyModule_Create(&metricsmodule);
    if (m == NULL)
        return NULL;
    
    Py_INCREF(&MetricsEngineType);
    if (PyModule_AddObject(m, "MetricsEngine", (PyObject *) &MetricsEngineType) < 0) {
        Py_DECREF(&MetricsEngineType);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}