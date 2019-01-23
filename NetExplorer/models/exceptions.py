from .common import *

# EXCEPTIONS
# ------------------------------------------------------------------------------
class IncorrectDatabase(Exception):
    """Exception raised when incorrect database"""
    def __init__(self, database):
        self.database = database

    def __str__(self):
        return "%s database not found, incorrect database name." % self.database

# ------------------------------------------------------------------------------
class WrongGraphObject(Exception):
    """Exception for wrong graph object given to add_[node|edge]"""
    def __init__(self, obj):
        self.type = type(obj)
    def __str__(self):
        return "Can't add object of type %s to GraphCytoscape object." % self.type

# ------------------------------------------------------------------------------
class NodeNotFound(Exception):
    """Exception raised when a node is not found on the db"""
    def __init__(self, symbol, database):
        self.symbol   = symbol
        self.database = database
    def __str__(self):
        return "Symbol %s not found in database %s." % (self.symbol, self.database)

# ------------------------------------------------------------------------------
class NoExpressionData(Exception):
    """Exception node has no expression data"""
    def __init__(self, symbol, database, experiment, sample):
        self.symbol     = symbol
        self.database   = database
        self.experiment = experiment
        self.sample     = sample
    def __str__(self):
        return "Expression for experiment %s and sample %s not found for node %s of database %s" % (self.experiment, self.sample, self.symbol, self.database)

# ------------------------------------------------------------------------------
class ExperimentNotFound(Exception):
    """
    Exception thrown when trying to create a experiment object that was not found on the DB
    """
    def __init__(self, experiment):
        self.experiment = experiment
    def __str__(self):
        return "Experiment %s not found in database" % self.experiment

# ------------------------------------------------------------------------------
class SampleNotAvailable(Exception):
    """Exception raised when a specified sample is not found for a particular experiment"""
    def __init__(self, experiment, sample):
        self.experiment = experiment
        self.sample     = sample
    def __str__(self):
        return "Sample %s not found for experiment %s in database" % (self.sample, self.experiment)

# ------------------------------------------------------------------------------
class NotGOAccession(Exception):
    """Exception when GO accession provided to GO object is not a GO accession"""
    def __init__(self, go_object):
        self.go = go_object
    def __str__(self):
        return "GO accession: %s is not an allowed GO accession (GO:\\d{7})" % (self.go.accession)

# ------------------------------------------------------------------------------
class NotPFAMAccession(Exception):
    """Exception when PFAM accession provided to GO object is not a GO accession"""
    def __init__(self, acc):
        self.acc = acc
    def __str__(self):
        return "PFAM accession: %s is not an allowed PFAM accession (PFAM:\\d{7})" % (self.acc)

# ------------------------------------------------------------------------------
class NoHomologFound(Exception):
    """Exception raised when a node homolog is not found. Internal error. Should not happen"""
    def __init__(self, symbol):
        self.symbol = symbol
    def __str__(self):
        return "Homolog of %s not found in database." % (self.symbol)

class InvalidFormat(Exception):
    """Exception raised when format for ServedFile is invalid"""
    def __init__(self, ffomat):
        self.fformat = fformat
    def __str__(self):
        return "Invalid file format: %s ." % (self.fformat)


