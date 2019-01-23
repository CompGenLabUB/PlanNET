import sys
import MySQLdb
import argparse

#--------------------------------------------------------------------------------
def get_options():
    parser = argparse.ArgumentParser(
        description='''Delete Expression experiments from PlanNET / PlanExp.''')

    parser.add_argument(
            '-n','--name',
            help='Experiment name', required=True
        )
    parser.add_argument(
        '-u','--user',
        help='Mysql user', required=True
    )
    parser.add_argument(
        '-p','--password',
        help='Mysql password', required=True
    )
    parser.add_argument(
        '-m','--mysql_db',
        help='Mysql database', required=True
    )
    options = parser.parse_args()
    return options


#--------------------------------------------------------------------------------
def connect_to_db(opts):
    db = MySQLdb.Connection(
        user=opts.user,
        passwd=opts.password,
        db=opts.mysql_db
    )
    return db

#--------------------------------------------------------------------------------
def get_experiment(opts, cursor):
    try:
        cursor.execute("""SELECT id FROM NetExplorer_experiment 
                          WHERE name = %s""", (opts.name, ))
        r = cursor.fetchone()
        return r[0]
    except TypeError:
        sys.stderr.write("Experiment %s does not exist in database!\n" % opts.name)

#--------------------------------------------------------------------------------
def delete_absolute_expression(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_expressionabsolute
        WHERE experiment_id=%s
    """, (experiment,))

def delete_relative_expression(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_expressionrelative
        WHERE experiment_id=%s
    """, (experiment,))


def delete_experimentdataset(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_experimentdataset
        WHERE experiment_id=%s
    """, (experiment,))

def delete_userexperimentpermission(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_userexperimentpermission
        WHERE experiment_id=%s
    """, (experiment,))

def delete_samplecondition(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_samplecondition
        WHERE experiment_id=%s
    """, (experiment,))

def delete_sample(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_sample
        WHERE experiment_id=%s
    """, (experiment,))

def delete_condition(opts, experiment):
    cursor.execute("""
        DELETE FROM NetExplorer_condition
        WHERE experiment_id=%s
    """, (experiment,))


#--------------------------------------------------------------------------------
# MAIN

opts = get_options()
db = connect_to_db(opts)
cursor = db.cursor()

sys.stderr.write("Getting experiment from database.\n")
experiment = get_experiment(opts, cursor)

sys.stderr.write("Deleting absolute expression.\n")
delete_absolute_expression(opts, experiment)

sys.stderr.write("Deleting relative expression.\n")
delete_relative_expression(opts, experiment)

sys.stderr.write("Deleting experiment-dataset.\n")
delete_experimentdataset(opts, experiment)

sys.stderr.write("Deleting user-experiment-permission.\n")
delete_userexperimentpermission(opts, experiment)

sys.stderr.write("Deleting sample.\n")
delete_sample(opts, experiment)

sys.stderr.write("Deleting sample-condition.\n")
delete_samplecondition(opts, experiment)

sys.stderr.write("Deleting condition.\n")
delete_condition(opts, experiment)


sys.stderr.write("All done.\n")
db.commit()







