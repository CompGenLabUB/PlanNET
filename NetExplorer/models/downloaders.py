from .common import *

# ------------------------------------------------------------------------------
class DownloadHandler(object):
    '''
    Class that handles downloadable files.

    Attributes:
        data_from_node: Class attribute, dictionary mapping data type keywords, 
            to the methods that handle them.
            {'contig'
             'orf'
             'homology'
             'pfam'
             'go'
             'interactions'}
    Usage:
        dhandler = DownloadHandler()
        the_file = dhandler.download_data(identifiers, database, data)
        response = the_file.to_response()
    

    Methods get_*_data returns a list of tuples, each tuple being a line, and each
    element of the tuple being a column.
    '''
    def _get_contig_data(node):
        if not node.sequence:
            node.get_all_information()
        return [(node.symbol, node.sequence, node.database)]

    def _get_orf_data(node):
        if not node.orf:
            node.get_all_information()
        return [(node.symbol, node.orf, node.database)]

    def _get_homology_data(node):
        return [(node.symbol, node.homolog.human.symbol, 
                node.homolog.blast_eval, node.homolog.blast_cov, 
                node.homolog.nog_eval, node.homolog.pfam_sc)]

    def _get_pfam_data(node):
        node.get_domains()
        if node.domains:
            domains = ";".join([ "%s:%s-%s"  % (str(dom.domain.accession), str(dom.s_start), str(dom.s_end)) for dom in node.domains ])
        else:
            domains = "NA"
        return([(node.symbol, domains)])

    def _get_go_data(node):
        node.get_geneontology()
        gos = ";".join([ go.accession for go in node.gene_ontologies ])
        return [(node.symbol, gos)]

    def _get_interactions_data(node):
        node.get_neighbours()
        ints = [ ( node.symbol, interaction.target.symbol, str(interaction.parameters['int_prob']) ) 
                 for interaction in node.neighbours ]
        return(ints)

    data_from_node = {
        'contig': _get_contig_data,
        'orf': _get_orf_data,
        'homology': _get_homology_data,
        'pfam': _get_pfam_data,
        'go': _get_go_data,
        'interactions': _get_interactions_data
    }

    def download_data(self, identifiers, database, data):
        '''
        Creates file object with the specified data for the
        specified identifiers.
        '''
        fformat = 'csv'
        if data == "contig" or data == "orf":
            fformat = 'fasta'
        dfile = ServedFile(self.get_filename(data), fformat, self.get_header(data))
        for identifier in identifiers:
            try:
                gsearch = GeneSearch(identifier, database)
                nodes = gsearch.get_planarian_contigs()
                for node in nodes:
                    dfile.add_elements(self.data_from_node[data](node))
            except exceptions.NodeNotFound:
                continue
        return dfile

    def get_filename(self, data):
        '''
        Returns filename string
        '''
        if data == "contig" or data=="orf":
            filename = "fasta.fa"
        elif data == "homology":
            filename = "homologs.csv"
        elif data == "pfam":
            filename = "domains.csv"
        elif data == "interactions":
            filename = "interactions.csv"
        else:
            filename = "gene_ontologies.csv"
        return filename

    def get_header(self, data):
        '''
        Returns header string
        '''
        if data == "homology":
            header = "NAME,HUMAN,BLAST_EVALUE,BLAST_COVERAGE,EGGNOG_EVALUE,META_ALIGNMENT_SCORE\n"
        else:
            header = None
        return header


# ------------------------------------------------------------------------------
class ServedFile(object):
    '''
    Class of served files for download.

    Attributes:
        oname: String with output filename.
        fformat: String with file format, can be 'csv' or 'fasta'.
        header: Bool describing if file should have a header.
        written: Bool describing if the file has data on it or not.
    '''
    def __init__(self, oname, fformat='csv', header=None):
        self.oname = oname
        self.fformat = fformat
        self.header = header
        self.filename = tempfile.NamedTemporaryFile()
        self.elements = list()
        self.written = False

    def add_elements(self, elem):
        '''
        Adds a register to the list of elements
        '''
        self.elements.extend(elem)

    def write(self, what=None):
        '''
        Writes to temp file
        '''
        with open(self.filename.name, "w") as fh:
            if self.header is not None:
                fh.write(self.header)
            for elem in self.elements:
                if self.fformat == 'csv':
                    fh.write( "%s\n" % ",".join(elem) )
                elif self.fformat == 'fasta':
                    formatseq = "".join(elem[1][i:i+64] + "\n" for i in range(0,len(elem[1]), 64)) 
                    fh.write(">%s|%s\n%s" % (elem[0], elem[2], formatseq))
                else:
                    raise InvalidFormat(self.fformat)
        self.written = True

    def to_response(self, what=None):
        '''
        Creates a response object to be served to the user for download
        '''
        if self.written is False:
            self.write(what)
        wrapper = FileWrapper(open(self.filename.name))
        response = HttpResponse(wrapper, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % self.oname
        response['Content-Length'] = os.path.getsize(self.filename.name)
        return response


from NetExplorer.models import exceptions