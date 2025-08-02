/*
 * Python C API wrapper for Django Mercury Query Analyzer
 * Analyzes SQL queries for performance issues
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include <ctype.h>

/* Query Analyzer Structure */
typedef struct {
    PyObject_HEAD
    int total_queries_analyzed;
} QueryAnalyzer;

/* Helper function to check if string contains substring (case-insensitive) */
static int
contains_case_insensitive(const char *haystack, const char *needle)
{
    if (!haystack || !needle) return 0;
    
    size_t haystack_len = strlen(haystack);
    size_t needle_len = strlen(needle);
    
    if (needle_len > haystack_len) return 0;
    
    for (size_t i = 0; i <= haystack_len - needle_len; i++) {
        int match = 1;
        for (size_t j = 0; j < needle_len; j++) {
            if (tolower(haystack[i + j]) != tolower(needle[j])) {
                match = 0;
                break;
            }
        }
        if (match) return 1;
    }
    return 0;
}

/* Destructor */
static void
QueryAnalyzer_dealloc(QueryAnalyzer *self)
{
    Py_TYPE(self)->tp_free((PyObject *) self);
}

/* Constructor */
static PyObject *
QueryAnalyzer_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    QueryAnalyzer *self;
    self = (QueryAnalyzer *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->total_queries_analyzed = 0;
    }
    return (PyObject *) self;
}

/* Initialize */
static int
QueryAnalyzer_init(QueryAnalyzer *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

/* Analyze query method */
static PyObject *
QueryAnalyzer_analyze_query(QueryAnalyzer *self, PyObject *args)
{
    const char *sql;
    
    if (!PyArg_ParseTuple(args, "s", &sql)) {
        return NULL;
    }
    
    self->total_queries_analyzed++;
    
    PyObject *analysis = PyDict_New();
    if (analysis == NULL) {
        return NULL;
    }
    
    /* Analyze query type */
    const char *query_type = "UNKNOWN";
    if (contains_case_insensitive(sql, "SELECT")) {
        query_type = "SELECT";
    } else if (contains_case_insensitive(sql, "INSERT")) {
        query_type = "INSERT";
    } else if (contains_case_insensitive(sql, "UPDATE")) {
        query_type = "UPDATE";
    } else if (contains_case_insensitive(sql, "DELETE")) {
        query_type = "DELETE";
    }
    
    /* Check for potential performance issues */
    PyObject *issues = PyList_New(0);
    
    /* Check for SELECT * */
    if (contains_case_insensitive(sql, "SELECT *")) {
        PyList_Append(issues, PyUnicode_FromString("Uses SELECT * which fetches all columns"));
    }
    
    /* Check for missing WHERE clause in UPDATE/DELETE */
    if ((contains_case_insensitive(sql, "UPDATE") || contains_case_insensitive(sql, "DELETE")) &&
        !contains_case_insensitive(sql, "WHERE")) {
        PyList_Append(issues, PyUnicode_FromString("UPDATE/DELETE without WHERE clause"));
    }
    
    /* Check for LIKE with leading wildcard */
    if (contains_case_insensitive(sql, "LIKE '%")) {
        PyList_Append(issues, PyUnicode_FromString("LIKE with leading wildcard prevents index usage"));
    }
    
    /* Check for OR conditions */
    if (contains_case_insensitive(sql, " OR ")) {
        PyList_Append(issues, PyUnicode_FromString("OR conditions may prevent index optimization"));
    }
    
    /* Check for NOT IN */
    if (contains_case_insensitive(sql, "NOT IN")) {
        PyList_Append(issues, PyUnicode_FromString("NOT IN can be slow with large datasets"));
    }
    
    /* Check for subqueries */
    int paren_count = 0;
    int has_subquery = 0;
    for (const char *p = sql; *p; p++) {
        if (*p == '(') paren_count++;
        if (*p == ')') paren_count--;
        if (paren_count > 0 && contains_case_insensitive(p, "SELECT")) {
            has_subquery = 1;
            break;
        }
    }
    if (has_subquery) {
        PyList_Append(issues, PyUnicode_FromString("Contains subquery which may impact performance"));
    }
    
    /* Calculate complexity score (0-100) */
    int complexity = 10;  /* Base complexity */
    
    /* Add complexity for various factors */
    if (contains_case_insensitive(sql, "JOIN")) complexity += 15;
    if (contains_case_insensitive(sql, "LEFT JOIN")) complexity += 20;
    if (contains_case_insensitive(sql, "GROUP BY")) complexity += 15;
    if (contains_case_insensitive(sql, "ORDER BY")) complexity += 10;
    if (contains_case_insensitive(sql, "HAVING")) complexity += 15;
    if (has_subquery) complexity += 25;
    if (contains_case_insensitive(sql, "UNION")) complexity += 20;
    
    if (complexity > 100) complexity = 100;
    
    /* Check for potential index usage */
    int likely_uses_index = 0;
    if (contains_case_insensitive(sql, "WHERE") && 
        contains_case_insensitive(sql, "=") &&
        !contains_case_insensitive(sql, "LIKE")) {
        likely_uses_index = 1;
    }
    
    /* Build analysis result */
    PyDict_SetItemString(analysis, "query_type", PyUnicode_FromString(query_type));
    PyDict_SetItemString(analysis, "complexity_score", PyLong_FromLong(complexity));
    PyDict_SetItemString(analysis, "issues", issues);
    PyDict_SetItemString(analysis, "likely_uses_index", PyBool_FromLong(likely_uses_index));
    PyDict_SetItemString(analysis, "has_joins", 
                        PyBool_FromLong(contains_case_insensitive(sql, "JOIN")));
    PyDict_SetItemString(analysis, "has_subquery", PyBool_FromLong(has_subquery));
    PyDict_SetItemString(analysis, "implementation", PyUnicode_FromString("c_extension"));
    
    return analysis;
}

/* Method definitions */
static PyMethodDef QueryAnalyzer_methods[] = {
    {"analyze_query", (PyCFunction) QueryAnalyzer_analyze_query, METH_VARARGS,
     "Analyze a SQL query for performance issues"},
    {NULL}  /* Sentinel */
};

/* Type definition */
static PyTypeObject QueryAnalyzerType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "django_mercury._c_analyzer.QueryAnalyzer",
    .tp_doc = "C-based query analyzer for Django Mercury",
    .tp_basicsize = sizeof(QueryAnalyzer),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = QueryAnalyzer_new,
    .tp_init = (initproc) QueryAnalyzer_init,
    .tp_dealloc = (destructor) QueryAnalyzer_dealloc,
    .tp_methods = QueryAnalyzer_methods,
};

/* Module definition */
static PyModuleDef analyzermodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_c_analyzer",
    .m_doc = "C extension for Django Mercury query analyzer",
    .m_size = -1,
};

/* Module initialization */
PyMODINIT_FUNC
PyInit__c_analyzer(void)
{
    PyObject *m;
    
    if (PyType_Ready(&QueryAnalyzerType) < 0)
        return NULL;
    
    m = PyModule_Create(&analyzermodule);
    if (m == NULL)
        return NULL;
    
    Py_INCREF(&QueryAnalyzerType);
    if (PyModule_AddObject(m, "QueryAnalyzer", (PyObject *) &QueryAnalyzerType) < 0) {
        Py_DECREF(&QueryAnalyzerType);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}