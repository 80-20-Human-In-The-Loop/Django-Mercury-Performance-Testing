/*
 * Python C API wrapper for Django Mercury Test Orchestrator
 * Manages test execution and performance tracking
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

/* Cross-platform timing support */
#include "common.h"  /* This includes windows_compat.h which has gettimeofday for Windows */
#ifndef _WIN32
    #include <sys/time.h>
#endif

/* Test info structure */
typedef struct TestInfo {
    char *name;
    struct timeval start_time;
    struct timeval end_time;
    double duration_ms;
    int status;  /* 0=pending, 1=running, 2=passed, 3=failed */
    struct TestInfo *next;
} TestInfo;

/* Test Orchestrator Structure */
typedef struct {
    PyObject_HEAD
    TestInfo *tests;
    TestInfo *current_test;
    int total_tests;
    int passed_tests;
    int failed_tests;
} TestOrchestrator;

/* Helper to free test list */
static void
free_test_list(TestInfo *test)
{
    while (test) {
        TestInfo *next = test->next;
        if (test->name) {
            free(test->name);
        }
        free(test);
        test = next;
    }
}

/* Helper to find test by name */
static TestInfo *
find_test(TestInfo *tests, const char *name)
{
    TestInfo *current = tests;
    while (current) {
        if (current->name && strcmp(current->name, name) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

/* Destructor */
static void
TestOrchestrator_dealloc(TestOrchestrator *self)
{
    free_test_list(self->tests);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/* Constructor */
static PyObject *
TestOrchestrator_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    TestOrchestrator *self;
    self = (TestOrchestrator *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->tests = NULL;
        self->current_test = NULL;
        self->total_tests = 0;
        self->passed_tests = 0;
        self->failed_tests = 0;
    }
    return (PyObject *) self;
}

/* Initialize */
static int
TestOrchestrator_init(TestOrchestrator *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

/* Start test method */
static PyObject *
TestOrchestrator_start_test(TestOrchestrator *self, PyObject *args)
{
    const char *test_name;
    
    if (!PyArg_ParseTuple(args, "s", &test_name)) {
        return NULL;
    }
    
    /* Check if test already exists */
    TestInfo *existing = find_test(self->tests, test_name);
    if (existing) {
        /* Reset existing test */
        gettimeofday(&existing->start_time, NULL);
        existing->status = 1;  /* running */
        self->current_test = existing;
    } else {
        /* Create new test */
        TestInfo *new_test = (TestInfo *)malloc(sizeof(TestInfo));
        if (!new_test) {
            PyErr_SetString(PyExc_MemoryError, "Failed to allocate test info");
            return NULL;
        }
        
        new_test->name = malloc(strlen(test_name) + 1);
        if (!new_test->name) {
            /* Memory allocation failed - clean up and return error */
            free(new_test);
            PyErr_SetString(PyExc_MemoryError, "Failed to allocate test name");
            return NULL;
        }
        strcpy(new_test->name, test_name);
        
        gettimeofday(&new_test->start_time, NULL);
        new_test->duration_ms = 0.0;
        new_test->status = 1;  /* running */
        new_test->next = self->tests;
        
        self->tests = new_test;
        self->current_test = new_test;
        self->total_tests++;
    }
    
    Py_RETURN_NONE;
}

/* End test method */
static PyObject *
TestOrchestrator_end_test(TestOrchestrator *self, PyObject *args)
{
    const char *test_name;
    const char *status = "passed";
    
    if (!PyArg_ParseTuple(args, "s|s", &test_name, &status)) {
        return NULL;
    }
    
    TestInfo *test = find_test(self->tests, test_name);
    if (!test) {
        PyErr_SetString(PyExc_ValueError, "Test not found");
        return NULL;
    }
    
    gettimeofday(&test->end_time, NULL);
    
    /* Calculate duration */
    double elapsed = (test->end_time.tv_sec - test->start_time.tv_sec) * 1000.0;
    elapsed += (test->end_time.tv_usec - test->start_time.tv_usec) / 1000.0;
    test->duration_ms = elapsed;
    
    /* Set status */
    if (strcmp(status, "passed") == 0) {
        test->status = 2;
        self->passed_tests++;
    } else {
        test->status = 3;
        self->failed_tests++;
    }
    
    if (self->current_test == test) {
        self->current_test = NULL;
    }
    
    /* Return test result */
    PyObject *result = PyDict_New();
    if (result == NULL) {
        return NULL;
    }
    
    PyDict_SetItemString(result, "name", PyUnicode_FromString(test_name));
    PyDict_SetItemString(result, "duration_ms", PyFloat_FromDouble(test->duration_ms));
    PyDict_SetItemString(result, "status", PyUnicode_FromString(status));
    PyDict_SetItemString(result, "implementation", PyUnicode_FromString("c_extension"));
    
    return result;
}

/* Get summary method */
static PyObject *
TestOrchestrator_get_summary(TestOrchestrator *self, PyObject *Py_UNUSED(ignored))
{
    PyObject *summary = PyDict_New();
    if (summary == NULL) {
        return NULL;
    }
    
    /* Calculate total duration and collect test details */
    double total_duration = 0.0;
    int running_tests = 0;
    PyObject *test_list = PyList_New(0);
    
    TestInfo *current = self->tests;
    while (current) {
        if (current->status == 2 || current->status == 3) {
            total_duration += current->duration_ms;
        }
        if (current->status == 1) {
            running_tests++;
        }
        
        /* Add test to list */
        PyObject *test_dict = PyDict_New();
        PyDict_SetItemString(test_dict, "name", PyUnicode_FromString(current->name));
        PyDict_SetItemString(test_dict, "duration_ms", PyFloat_FromDouble(current->duration_ms));
        
        const char *status_str = "pending";
        switch (current->status) {
            case 1: status_str = "running"; break;
            case 2: status_str = "passed"; break;
            case 3: status_str = "failed"; break;
        }
        PyDict_SetItemString(test_dict, "status", PyUnicode_FromString(status_str));
        
        PyList_Append(test_list, test_dict);
        Py_DECREF(test_dict);
        
        current = current->next;
    }
    
    /* Calculate average duration */
    double avg_duration = 0.0;
    int completed = self->passed_tests + self->failed_tests;
    if (completed > 0) {
        avg_duration = total_duration / completed;
    }
    
    /* Calculate pass rate */
    double pass_rate = 0.0;
    if (completed > 0) {
        pass_rate = (double)self->passed_tests / completed * 100.0;
    }
    
    PyDict_SetItemString(summary, "total_tests", PyLong_FromLong(self->total_tests));
    PyDict_SetItemString(summary, "passed", PyLong_FromLong(self->passed_tests));
    PyDict_SetItemString(summary, "failed", PyLong_FromLong(self->failed_tests));
    PyDict_SetItemString(summary, "running", PyLong_FromLong(running_tests));
    PyDict_SetItemString(summary, "total_duration_ms", PyFloat_FromDouble(total_duration));
    PyDict_SetItemString(summary, "average_duration_ms", PyFloat_FromDouble(avg_duration));
    PyDict_SetItemString(summary, "pass_rate", PyFloat_FromDouble(pass_rate));
    PyDict_SetItemString(summary, "tests", test_list);
    PyDict_SetItemString(summary, "implementation", PyUnicode_FromString("c_extension"));
    
    return summary;
}

/* Method definitions */
static PyMethodDef TestOrchestrator_methods[] = {
    {"start_test", (PyCFunction) TestOrchestrator_start_test, METH_VARARGS,
     "Start tracking a test"},
    {"end_test", (PyCFunction) TestOrchestrator_end_test, METH_VARARGS,
     "End tracking a test"},
    {"get_summary", (PyCFunction) TestOrchestrator_get_summary, METH_NOARGS,
     "Get test execution summary"},
    {NULL}  /* Sentinel */
};

/* Type definition */
static PyTypeObject TestOrchestratorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "django_mercury._c_orchestrator.TestOrchestrator",
    .tp_doc = "C-based test orchestrator for Django Mercury",
    .tp_basicsize = sizeof(TestOrchestrator),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = TestOrchestrator_new,
    .tp_init = (initproc) TestOrchestrator_init,
    .tp_dealloc = (destructor) TestOrchestrator_dealloc,
    .tp_methods = TestOrchestrator_methods,
};

/* Module definition */
static PyModuleDef orchestratormodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_c_orchestrator",
    .m_doc = "C extension for Django Mercury test orchestrator",
    .m_size = -1,
};

/* Module initialization */
PyMODINIT_FUNC
PyInit__c_orchestrator(void)
{
    PyObject *m;
    
    if (PyType_Ready(&TestOrchestratorType) < 0)
        return NULL;
    
    m = PyModule_Create(&orchestratormodule);
    if (m == NULL)
        return NULL;
    
    Py_INCREF(&TestOrchestratorType);
    if (PyModule_AddObject(m, "TestOrchestrator", (PyObject *) &TestOrchestratorType) < 0) {
        Py_DECREF(&TestOrchestratorType);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}