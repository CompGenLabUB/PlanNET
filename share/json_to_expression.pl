#!/usr/bin/perl

use warnings;
use strict;
use JSON;
use Data::Dumper;
use Getopt::Long;

#--------------------------------------------------------------------------------
# FUNCTIONS
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
sub print_help {
    print <<EOF

    json_to_expression.pl - convert json files from DGE experiment to tabular files for planexp

        OPTIONS:
            -h 
                Shows this help.
            
            -name STRING
                Experiment name.
            
            -dataset STRING
                Dataset (transcriptome) name.

            -json FILE
                JSON file with expression data.

            -odir DIRECTORY
                Output directory.

        OUTPUT:
            - Absolute expression file:
                ROWS
                      Each row is an expression for a given sample and a given gene.
                COLUMNS
                      1- Experiment name.
                      2- Condition list for sample (separated by commas).
                      3- Condition types (separated by commas).
                      4- Dataset.
                      5- Sample name.
                      6- Gene/Contig symbol.
                      7- Expression value.
                      8- Units.
            - Relative expression file:
                ROWS
                    Each row is a comparison between two conditions (fold change + pvalue).
                COLUMNS
                    1- Experiment name.
                    2- Condition 1 name.
                    3- Condition 2 name.
                    4- Condition type for 1 and 2.
                    5- Dataset.
                    6- Gene/Contig symbol.
                    7- Fold change.
                    8- P-value.
                        
EOF
;
    return;
}

#--------------------------------------------------------------------------------
sub read_json {
    my $file = shift;
    my $json = "";

    open my $fh, "<", $file
        or die "Can't open file : $!\n";
    while (<$fh>) {
        chomp;
        $json .= $_;
    }
    my $exp_data = decode_json($json);
    return $exp_data;
}

#--------------------------------------------------------------------------------
sub fold_change {
    my $a = shift;
    my $b = shift;
    # Add pseudocounts
    $a += 0.001;
    $b += 0.001;
    return log($a / $b) / log(2);
}


#--------------------------------------------------------------------------------
# MAIN
#--------------------------------------------------------------------------------

my %options = ();
GetOptions (
        \%options    ,
        'help|?'     ,
        'name=s'     ,   
        'dataset=s'  ,
        'json=s'     ,
        'odir=s'     
);

if (defined $options{'help'}) {
    print_help();
    exit(0);
}

if (not defined $options{'name'}) {
    die "Please, define experiment name with option -name\n";
}

if (not defined $options{'dataset'}) {
    die "Please, define dataset with option -dataset\n";
}

if (not defined $options{'json'}) {
    die "Please, define json file with option -json\n";
}

if (not defined $options{'odir'}) {
    $options{'odir'} = ".";
}


# START

my $data = read_json($options{'json'});

my $absolute_file = $options{'odir'} . "/" . $options{'name'} . "_" . $options{'dataset'} . "_" . "absolute.tbl";
my $relative_file = $options{'odir'} . "/" . $options{'name'} . "_" . $options{'dataset'} . "_" . "relative.tbl";

open my $afh, ">", $absolute_file
    or die "Can't open $absolute_file : $!\n";

open my $rfh, ">", $relative_file
    or die "Can't open $relative_file : $!\n";

print $afh join("\t", qw(Experiment_NAME CONDITION_NAME CONDITION_TYPE DATASET SAMPLE_ID GENE_SYMBOL EXP_VALUE UNITS)), "\n";
print $rfh join("\t", qw(Experiment_NAME CONDITION1_NAME CONDITION2_NAME CONDITION_TYPE DATASET GENE_SYMBOL FOLD_CHANGE PVALUE)), "\n";
foreach my $transcript (@{ $data->{rows} }) {
    my ($gene, $strand, 
        $X1, $X2, $Xin, 
        $control, $irradiated, 
        $pval_X1_Xin, $pval_X2_Xin, $pval_X1_X2) = @{ $transcript->{'cell'} }[0..9];
    my $fc_X1_Xin = fold_change($X1, $Xin);
    my $fc_X2_Xin = fold_change($X2, $Xin);
    my $fc_X1_X2  = fold_change($X1, $X2);
    # AFH: Experiment_NAME | CONDITION_NAME | CONDITION_TYPE | DATASET | SAMPLE_ID | GENE_SYMBOL | EXP_VALUE | UNITS
    print $afh join("\t", ($options{'name'}, "X1", "Experimental", $options{'dataset'}, "X1", $gene, $X1, "cpm")), "\n";
    print $afh join("\t", ($options{'name'}, "X2", "Experimental", $options{'dataset'}, "X2", $gene, $X2, "cpm")), "\n";
    print $afh join("\t", ($options{'name'}, "Xin", "Experimental", $options{'dataset'},"Xin",  $gene, $Xin, "cpm")), "\n";

    # RFH: Experiment_NAME | CONDITION1_NAME | CONDITION2_NAME | CONDITION_TYPE | DATASET | GENE_SYMBOL | FOLD_CHANGE | PVALUE
    print $rfh join("\t", ($options{'name'}, "X1", "Xin", "Experimental", $options{'dataset'}, $gene, $fc_X1_Xin, $pval_X1_Xin)), "\n";
    print $rfh join("\t", ($options{'name'}, "X2", "Xin", "Experimental", $options{'dataset'}, $gene, $fc_X2_Xin, $pval_X2_Xin)), "\n";
    print $rfh join("\t", ($options{'name'}, "X1", "X2", "Experimental", $options{'dataset'}, $gene, $fc_X1_X2, $pval_X1_X2)), "\n";
}

close($afh);
close($rfh);