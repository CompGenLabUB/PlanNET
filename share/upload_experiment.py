import sys
import MySQLdb
import argparse
import textwrap

def get_options():
    '''
    Reads the options
    '''
    parser = argparse.ArgumentParser(
        description='''Upload Expression experiments to PlanNET / PlanExp.''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
        input files:
            - Absolute expression file (-a):
                ROWS
                      Each row is an expression for a given sample and a given gene.
                      Header required.
                COLUMNS
                      1- Experiment name.
                      2- Condition list for sample (separated by commas).
                      3- Condition types (separated by commas).
                      4- Dataset.
                      5- Sample name.
                      6- Gene/Contig symbol.
                      7- Expression value.
                      8- Units.

            - Relative expression file (-r):
                ROWS
                    Each row is a comparison between two conditions for a given gene 
                    (fold change + pvalue).
                    Header required.
                COLUMNS
                    1- Experiment name.
                    2- Condition 1 name.
                    3- Condition 2 name.
                    4- Condition type for 1 and 2.
                    5- Dataset.
                    6- Gene/Contig symbol.
                    7- Fold change.
                    8- P-value.
        
        notes:
            Remember that the Experiment, the Conditions and the ConditionTypes 
            must already be on the database.
        '''))
    parser.add_argument(
        '-n','--name',
        help='Experiment name', required=True
    )
    parser.add_argument(
        '-a','--absolute',
        help='Absolute expression file', required=True
    )
    parser.add_argument(
        '-r','--relative',
        help='Relative expression file', required=True
    )
    parser.add_argument(
        '-t','--tsne',
        help='TSNE file', required=True
    )
    parser.add_argument(
        '-d','--dataset',
        help='Dataset name', required=True
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
def get_dataset(opts, cursor):
    try:
        cursor.execute("""SELECT id FROM NetExplorer_dataset 
                          WHERE name = %s""", (opts.dataset, ))
        r = cursor.fetchone()
        return r[0]
    except TypeError:
        sys.stderr.write("Experiment %s does not exist in database!\n" % opts.dataset)

#--------------------------------------------------------------------------------
def upload_sample(experiment, sample_name):
    cursor.execute("""SELECT id, sample_name FROM NetExplorer_sample 
                      WHERE sample_name = %s""", (sample_name, ))
    r = cursor.fetchone()
    sample_id = None
    if r:
        sample_id = r[0]
    else:
        # Sample not in database
        cursor.execute("""INSERT INTO NetExplorer_sample (experiment_id, sample_name) 
                          VALUES (%s, %s)""", (experiment, sample_name))
        sample_id = cursor.lastrowid
    return sample_id

#--------------------------------------------------------------------------------
def get_condition_id(experiment, condition):
    cursor.execute("""SELECT id FROM NetExplorer_condition
                      WHERE experiment_id = %s AND name = %s""", (experiment, condition))
    r = cursor.fetchone()
    return r[0]

#--------------------------------------------------------------------------------
def upload_sample_membership(experiment, sample_id, condition_id):
    cursor.execute("""SELECT experiment_id, sample_id, condition_id FROM NetExplorer_samplecondition
                      WHERE experiment_id = %s 
                      AND   sample_id = %s
                      AND   condition_id = %s""", (experiment, sample_id, condition_id))
    r = cursor.fetchone()
    if not r:
        # Upload Sample ~ Condition relationship
        cursor.execute("""
            INSERT INTO NetExplorer_samplecondition (experiment_id, sample_id, condition_id)
            VALUES (%s, %s, %s)""", (experiment, sample_id, condition_id))

#--------------------------------------------------------------------------------
def store_expression_absolute(experiment_id, sample_id, dataset_id, gene_symbol, expression, units):
    cursor.execute("""
        INSERT INTO NetExplorer_expressionabsolute (experiment_id, sample_id, dataset_id, gene_symbol, expression_value, units)
        VALUES (%s, %s, %s, %s, %s, %s)""", (experiment_id, sample_id, dataset_id, gene_symbol, expression, units))

#--------------------------------------------------------------------------------
def upload_expression_absolute(opts, experiment, dataset_id):
    with open(opts.absolute, "r") as abs_fh:
        next(abs_fh) # Skip first line
        for line in abs_fh:
            if line.startswith("#"):
                next
            line = line.strip()
            cols = line.split("\t")
            sample_name = cols[4]
            sample_id = upload_sample(experiment, sample_name)
            conditions = cols[1].split(",")
            for cond in conditions:
                condition_id = get_condition_id(experiment, cond)
                upload_sample_membership(experiment, sample_id, condition_id)
            store_expression_absolute(experiment, sample_id, dataset_id, cols[5], cols[6], cols[7])

#--------------------------------------------------------------------------------
def get_condition_type(name):
    cursor.execute("""SELECT id, name FROM NetExplorer_conditiontype
                      WHERE name = %s""", (name, ))
    r = cursor.fetchone()
    return r[0]

#--------------------------------------------------------------------------------
def store_expression_relative(experiment_id, c1_id, c2_id, ctype_id, dataset_id, gene_symbol, fc, pval):
    cursor.execute("""
        INSERT INTO NetExplorer_expressionrelative (experiment_id, condition1_id, condition2_id, cond_type_id, dataset_id, gene_symbol, fold_change, pvalue)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (experiment_id, c1_id, c2_id, ctype_id, dataset_id, gene_symbol, fc, pval))

#--------------------------------------------------------------------------------
def upload_expression_relative(opts, experiment, dataset):
    # For each condition comparison
        # (get conditions) + Upload relative expression (ExpressionRelative)
    with open(opts.relative, "r") as rel_fh:
        next(rel_fh)
        for line in rel_fh:
            line = line.strip()
            cols = line.split("\t")
            condition1_id = get_condition_id(experiment, cols[1])
            condition2_id = get_condition_id(experiment, cols[2])
            cond_type = get_condition_type(cols[3])
            store_expression_relative(
                experiment, condition1_id, 
                condition2_id, cond_type, dataset, 
                cols[5], cols[6], cols[7])


def upload_tsne(opts, experiment, dataset):
    with open(opts.tsne, "r") as tsne_fh:
        for line in tsne_fh:
            line = line.strip()
            sample_name, x, y = line.split("\t")
            cursor.execute("""SELECT id, sample_name FROM NetExplorer_sample 
                              WHERE sample_name = %s""", (sample_name, ))
            r = cursor.fetchone()
            sample_id = r[0]
            cursor.execute("""INSERT INTO NetExplorer_cellplotposition (experiment_id, sample_id, dataset_id, x_position, y_position) 
            VALUES (%s, %s, %s, %s, %s)""", (experiment, sample_id, dataset, x, y))
            

# MAIN
#--------------------------------------------------------------------------------
sys.stderr.write("Reading options\n")
opts = get_options()

sys.stderr.write("Connecting to database.\n")
db = connect_to_db(opts)
cursor = db.cursor()

sys.stderr.write("Getting experiment from database.\n")
experiment = get_experiment(opts, cursor)

sys.stderr.write("Getting Dataset from database\n")
dataset = get_dataset(opts, cursor)

sys.stderr.write("Uploading Absolute expression\n")
upload_expression_absolute(opts, experiment, dataset)

sys.stderr.write("Uploading relative expression\n")
upload_expression_relative(opts, experiment, dataset)

sys.stderr.write("Uploading cell plot positions (t-SNE)\n")
upload_tsne(opts, experiment, dataset)

sys.stderr.write("Committing to database\n")
db.commit()
