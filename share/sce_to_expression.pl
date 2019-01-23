#!/usr/bin/perl
use strict;
use warnings;
use Data::Dumper;

sub read_cellfile {
    my $file = shift;
    my %data = ();
    open my $fh, "<", $file
        or die "Can't open $file : $!\n";

    while (<$fh>) {
        chomp;
        my ($cell, $cluster, $batch, $dnac) = split /\t/;
        if (not exists $data{$cell}) {
            $data{$cell} = ();
            $data{$cell}{'CLUSTER'} = $cluster;
            $data{$cell}{'BATCH'}   = $batch;
            $data{$cell}{'DNAC'}    = $dnac;
        }

    }

    return \%data;
}

sub read_expfile {
    my $file = shift;
    my %data = ();

    open my $fh, "<", $file
        or die "Can't open $file : $!\n";
    
    my $header = <$fh>;
    chomp($header);
    my @cells = split /\t/, $header;
    while (<$fh>) {
        chomp;
        my ($gene, @expression) = split /\t/;
        foreach my $i (0 .. $#cells) {
            my $cell = $cells[$i];
            $data{$cell} = () unless exists $data{$cell};
            $data{$cell}{$gene} = $expression[$i];
        }
    }

    return \%data;
}


sub read_and_print_difffile {
    my $file     = shift;
    my $exp_name = shift;
    my $dataset  = shift;
    my $odir     = shift;
    my %data = ();
    my $ofile = $odir . "/" . $exp_name . "_" . $dataset . "_" . "relative.tbl";

    open my $fh, "<", $file
        or die "Can't open $file : $!\n";

    open my $ofh, ">", $ofile
        or die "Can't write to $ofile : $!\n";

    print $ofh "Experiment_NAME\tCONDITION1_NAME\tCONDITION2_NAME\tCONDITION_TYPE\tDATASET\tGENE_SYMBOL\tFOLD_CHANGE\tPVALUE\n";
    <$fh>; # skip header
    while (<$fh>) {
        chomp;
        my ($c1, $c2, $gene, $fc, $fdr, $junk) = split /\t/;
        print $ofh "$exp_name\t$c1\t$c2\tCluster\t$dataset\t$gene\t$fc\t$fdr\n";
    }

    return;
}



sub print_absolute {
    my $expression = shift;
    my $cell_conditions = shift;
    my $exp_name = shift;
    my $dataset = shift;
    my $odir = shift;
    my $ofile = $odir . "/" . $exp_name . "_" . $dataset . "_" . "absolute.tbl";

    open my $ofh, ">", $ofile
        or die "Can't write to $ofile : $!\n";
    
    print $ofh "Experiment_NAME\tCONDITION_NAME\tCONDITION_TYPE\tDATASET\tSAMPLE_ID\tGENE_SYMBOL\tEXP_VALUE\tUNITS\n";
    foreach my $cell (keys %{ $expression }) {
        my $conditions = "$cell_conditions->{$cell}{'BATCH'},$cell_conditions->{$cell}{'CLUSTER'},$cell_conditions->{$cell}{'DNAC'}";
        my $ctypes = "Batch,Cluster,Descriptive";

        foreach my $gene (keys %{ $expression->{$cell} }) {
            print $ofh "$exp_name\t$conditions\t$ctypes\t$dataset\t$cell\t$gene\t$expression->{$cell}{$gene}\tnormcounts\n";
        }
    }

    return;
}

die "Give me 5 arguments\n" unless scalar(@ARGV) == 6;
my $exp_name = shift @ARGV;
my $dataset  = shift @ARGV;
my $cellfile = shift @ARGV;
my $expfile  = shift @ARGV;
my $difffile = shift @ARGV;
my $odir     = shift @ARGV;

my $cell_conditions = read_cellfile($cellfile);
my $expression      = read_expfile($expfile);

print_absolute($expression, $cell_conditions, $exp_name, $dataset, $odir);
read_and_print_difffile($difffile, $exp_name, $dataset, $odir);