#!/usr/bin/perl

use warnings;
use strict;
use Getopt::Long;
use REST::Neo4p;
use Data::Dumper;
use IO::Zlib;

my %OPTS = ();
my $IP   = "http://localhost:7474";


# PARSE COMMAND LINE ARGUMENTS
GetOptions (
    \%OPTS         ,
    'help|?'       ,
    'human=s'      ,
    'species=s'    ,
    'fasta=s'      ,
    'length=s'     ,
    'pfamdb=s'     ,
    'dir=s'
 );


my $ORF_FILE      = $OPTS{'dir'} . "/ORFS/longestorfs.fa";
my $INT_FILE      = $OPTS{'dir'} . "/INTERACTOME.tbl";
my $PFAM_FILE     = $OPTS{'dir'} . "/PFAM/transcriptome_pfam.fix.tbl";
my $HOMOLOGY_FILE = $OPTS{'dir'} . "homologs.tbl";
my $PFAM_DBFILE   = $OPTS{'pfamdb'};

# START TIME
my $init_time  = localtime();
my $start_time = time();
print STDERR <<EOF
#
####### PROGRAM STARTED #######
# Start time: $init_time
# Connecting to $IP ...

EOF
;


die unless $OPTS{'species'};


if ($OPTS{'human'}) {
    upload_human($OPTS{'human'});
}

my %seq_info = ();
read_fasta(\%seq_info, $OPTS{fasta}, "sequence");
read_fasta(\%seq_info, $ORF_FILE,    "orf");
save_transcriptome(\%seq_info);

# Right now we can't upload homology information for all the sequences because the file
# is too big. We should create a "simpler" file with info_joiner so that we can use it here.
save_homology($HOMOLOGY_FILE);

save_interactome(\%seq_info, $INT_FILE);


if ($PFAM_DBFILE) {
    my %pfam_info = ();
    read_pfam(\%pfam_info, $PFAM_DBFILE);
    save_PFAM(\%pfam_info, $OPTS{'species'}, $PFAM_FILE);
}

my $end_time = localtime();
print STDERR <<EOF

#
####### PROGRAM FINISHED #######
# Finish time: $end_time

EOF
;


#===============================================================================
# FUNCTIONS
#===============================================================================

#--------------------------------------------------------------------------------
sub read_fasta {
    my $seq_info = shift;
    my $file     = shift;
    my $att_name = shift;

    open my $fh, "<", $file
        or die "Can't open $file : $!\n";

    local $/ = ">";
    <$fh>; #skip 1st line
    while (<$fh>) {
        chomp;
        my ($id, @seq) = split /\n/;
        $seq_info->{$id}->{$att_name} = join("", @seq);

        if ($att_name eq "sequence") {
            $seq_info->{$id}->{length} = length(join("", @seq));
        }
    }

    return;
}

#--------------------------------------------------------------------------------
sub save_transcriptome {
    my $seq_info = shift;

    open my $ofh, ">", "transcriptome.csv"
        or die "Can't create transcriptome.csv\n";

    print $ofh "symbol,sequence,orf,length\n";
    foreach my $node (keys %{ $seq_info }) {
        print $ofh "$node,$seq_info->{$node}->{sequence},$seq_info->{$node}->{orf},$seq_info->{$node}->{length}\n";
    }
    close($ofh);
    return;
}

#--------------------------------------------------------------------------------
sub save_homology {
    my $homology_file = shift;
    open my $fh, "<", $homology_file
        or die "Can't open $homology_file : $!\n";

    open my $ofh, ">", "homology.csv"
        or die "Can't create homology.csv\n";

    my %added = ();
    my $first_line = <$fh>;
    my $n = 1;
    print $ofh "symbol,human,blast_eval,blast_cov,blast_brh,nog_eval,nog_brh,pfam_sc,pfam_brh\n";
    while (<$fh>) {
        chomp;
        $n++;
        my ($symbol, $human, $blast_eval, $blast_cov, $blast_brh, $nog_eval, $nog_brh, $pfam_sc, $pfam_brh) = split /\t/;
        print $ofh "$symbol,$human,$blast_eval,$blast_cov,$blast_brh,$nog_eval,$nog_brh,$pfam_sc,$pfam_brh\n";
    }
    close($ofh);
    return;
}

#--------------------------------------------------------------------------------
sub save_interactome {
    my $seq_info   = shift;
    my $file       = shift;

    open my $fh, "<", $file
        or die "Can't open $file : $!\n";

    open my $ofh, ">", "interactions.csv"
        or die "Can't create interactions.csv\n";

    my $header = <$fh>;
    my ($h_tr1, $h_tr2, $h_hom1, $h_hom2, @h_features) = split /\t/, $header;
    my $n = 1;
    print $ofh "symbol1,symbol2,path_length,dom_int_sc,molfun_nto,bioproc_nto,cellcom_nto,int_prob\n";
    while (<$fh>) {
        chomp;
        print STDERR "Interaction number $n...\n";
        $n++;
        my ($tr1, $tr2, $hom1, $hom2, @features) = split /\t/, $_;
        print $ofh "$tr1,$tr2,$features[0],$features[15],$features[16],$features[17],$features[18],$features[20]\n";
    }
    return;
}

#--------------------------------------------------------------------------------
sub read_pfam {
    # Reads the Pfam-A.hmm.dat.gz file and saves the info about the domains.
    my $pfam_info = shift;
    my $file      = shift;


    local $/ = "//";
    open my $fh, "gzip -dc $file |"
        or die "Can't open $file :$!\n";

    DOMAIN:
    while (<$fh>) {
        chomp;
        my @fields = split /\n/;
        my %data = ();
        LINE:
        foreach my $field (@fields) {
            next LINE unless $field =~ m/^#=GF/;
            my ($junk, $entry_name, @value) = split /\s+/, $field; # Value is array because it may have spaces.
            next LINE unless $entry_name =~ m/ID|DE|AC|ML/;
            $data{$entry_name} = join(" ", @value);
        }
        if (%data) {
            $pfam_info->{ $data{"AC"} } = () unless exists $pfam_info->{$data{"AC"}};
            $pfam_info->{ $data{"AC"} }->{"ID"} = $data{"ID"};
            $pfam_info->{ $data{"AC"} }->{"DE"} = $data{"DE"};
            $pfam_info->{ $data{"AC"} }->{"ML"} = $data{"ML"};
        }
    }
    close $fh;

    return;
}


#--------------------------------------------------------------------------------
sub save_PFAM {
    # Reads PFAM file and uploads the necessary PFAM domains and edges.
    my $pfam_info = shift;
    my $species   = shift;
    my $pfam_file = shift;

    open my $fh, "<", $pfam_file
        or die "Can't open $pfam_file : $!\n";

    open my $dfh, ">", "domains.csv"
        or die "Can't create domains.csv\n";
    
    open my $sdfh, ">", "sequence_domains.csv"
        or die "Can't create equence_domains.csv\n";

    print STDERR "\n\n#Adding PFAM Domains\n";

    my $n = 1;
    print $dfh "accession,description,identifier,mlength\n";
    print $sdfh "symbol,accession,pfam_start,pfam_end,s_start,s_end,perc\n";
    while (<$fh>) {
        chomp;
        my ($seq, @domains) = split /\t/;
        foreach my $domain (@domains) {
            print "\tUploading domain number $n\n";
            $n++;
            my ($acc, $seq_coord, $pfam_coord, $perc) = split /\s+/, $domain;
            my ($pfam_start, $pfam_end) = split /\-/, $pfam_coord;
            my ($s_start, $s_end)       = split /\-/, $seq_coord;

            my $ident = $pfam_info->{$acc}->{"ID"};
            my $desc  = $pfam_info->{$acc}->{"DE"};
            my $mlen  = $pfam_info->{$acc}->{"ML"};

            print $dfh "$acc,$desc,$ident,$mlen\n";
            print $sdfh "$seq,$acc,$pfam_start,$pfam_end,$s_start,$s_end,$perc\n"; 

        }
    }
}
