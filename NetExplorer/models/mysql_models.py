from .common import *

# MODELS
# ------------------------------------------------------------------------------
class Dataset(models.Model):
    name = models.CharField(max_length=50)
    year = models.IntegerField(max_length=4)
    citation = models.CharField(max_length=512)
    url = models.URLField(max_length=200)
    n_contigs = models.IntegerField(max_length=1000000)
    n_ints = models.IntegerField(max_length=2000000)
    identifier_regex = models.CharField(max_length=200)
    public = models.BooleanField()

    def is_symbol_valid(self, symbol):
        '''
        Checks if a given symbol belongs to database based on 
        the symbol naming convention.
        '''
        if re.match(self.identifier_regex, symbol):
            return True
        else:
            return False

    @classmethod
    def get_allowed_datasets(cls, user):
        '''
        Returns QuerySet of allowed datasets for a given user
        '''
        public_datasets = cls.objects.filter(public=True).order_by('-year')
        if not user.is_authenticated:
            # Return only public datasets
            return public_datasets
        else:
            # user is authenticated, return allowed datasets
            restricted_allowed = cls.objects.filter(userdatasetpermission__user=user).order_by('-year')
            all_allowed = public_datasets | restricted_allowed
            return all_allowed
    
    def __str__(self):
       return self.name


# ------------------------------------------------------------------------------
class UserDatasetPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    def __str__(self):
       return self.user.username + " [access to] " + self.dataset.name


# ------------------------------------------------------------------------------
class ExperimentType(models.Model):
    exp_type = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
       return self.exp_type


# ------------------------------------------------------------------------------
class Experiment(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    citation = models.CharField(max_length=512)
    url = models.URLField(max_length=200)
    exp_type = models.ForeignKey(ExperimentType, on_delete=models.CASCADE)
    public = models.BooleanField()

    @classmethod
    def get_allowed_experiments(cls, user):
        '''
        Returns QuerySet of allowed experiments for a given user
        '''
        public_experiments = cls.objects.filter(public=True).order_by('name')
        if not user.is_authenticated:
            # Return only public datasets
            return public_experiments
        else:
            # user is authenticated, return allowed datasets
            restricted_allowed = cls.objects.filter(userexperimentpermission__user=user).order_by('name')
            all_allowed = public_experiments | restricted_allowed
            return all_allowed

    def to_json(self):
        '''
        Returns json string with info about experiment
        '''
        json_dict = {
            'name': self.name,
            'description': self.description,
            'citation': self.citation,
            'url': self.url,
            'type': self.exp_type.exp_type
        }
        conditions = Condition.objects.filter(experiment__name=self.name)
        json_dict['conditions'] = dict()
        for cond in conditions:
            if cond.cond_type.name not in json_dict['conditions']:
                json_dict['conditions'][cond.cond_type.name] = list()
            json_dict['conditions'][cond.cond_type.name].append( 
                (cond.name, cond.defines_cell_type, cond.cell_type, cond.description) 
            )
        json_string = json.dumps(json_dict)
        return json_string

    def __str__(self):
       return self.name

# ------------------------------------------------------------------------------
class ExperimentDataset(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    def __str__(self):
       return self.experiment.name + ' - ' + self.dataset.name


# ------------------------------------------------------------------------------
class UserExperimentPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    def __str__(self):
       return self.user.username + " [access to] " + self.experiment.name


# ------------------------------------------------------------------------------
class ConditionType(models.Model):
    '''
    1 Batch (technical condition).
    2 Experimental condition.
    3 Cluster.
    '''
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
       return self.name


# ------------------------------------------------------------------------------
class Condition(models.Model):
    '''
    Technical conditions, Experimental conditions, Clusters, and Cells will be stored here.
    '''
    name = models.CharField(max_length=50)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    cond_type = models.ForeignKey(ConditionType, on_delete=models.CASCADE)
    defines_cell_type = models.BooleanField()
    cell_type = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
       return self.name + " - " + self.experiment.name


# ------------------------------------------------------------------------------
class Sample(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample_name  = models.CharField(max_length=50)

    def __str__(self):
       return self.sample_name + " - " + self.experiment.name


# ------------------------------------------------------------------------------
class SampleCondition(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE)

    def __str__(self):
       return self.experiment.name + " - " + self.sample.sample_name + " - " + self.condition.name

# ------------------------------------------------------------------------------
class ExpressionAbsolute(models.Model):
    '''
    This table will store the expression value for each condition (for a given experiment and a given gene). 
    Keep in mind that a 'Condition' can be a Technical-Condition (0), Experimental-Condition (2), Cluster (3) or a Cell (4).
    In the case of 0, 1, 2, and 3 the expression will be the MEAN expression for that gene in those samples.
    In the case of 4 (a cell), the expression will be the actual expression in that particular cell. 
    The cell will have an entry in the 'Condition' table, just like any condition, linking it to a particular experiment.
    '''
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    gene_symbol = models.CharField(max_length=50)
    expression_value = models.FloatField()
    units = models.CharField(max_length=10)

    def __str__(self):
        name_str = self.experiment.name + " - "
        name_str += str(self.sample.sample_name) + " - "
        name_str += str(self.gene_symbol) + ": "
        name_str += str(self.expression_value) + " "
        name_str += self.units
        return name_str
    
    
class CellPlotPosition(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    x_position = models.FloatField()
    y_position = models.FloatField()


# ------------------------------------------------------------------------------
class ExpressionRelative(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    condition1 = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='condition1_expressionrelative_set')
    condition2 = models.ForeignKey(Condition, on_delete=models.CASCADE, related_name='condition1_expressionrelative_setsubcondition')
    cond_type = models.ForeignKey(ConditionType, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    gene_symbol = models.CharField(max_length=50)
    fold_change = models.FloatField()
    pvalue = models.FloatField()

    def __str__(self):
        name_str = self.experiment.name + " - "
        name_str += self.condition1.name + " vs "
        name_str += self.condition2.name + " - "
        name_str += str(self.gene_symbol) + ": "
        name_str += str(self.fold_change) + " "
        name_str += "(p=" + str(self.pvalue) + ")"
        return name_str
