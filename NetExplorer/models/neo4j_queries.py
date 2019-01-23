
# QUERIES
# ------------------------------------------------------------------------------
PREDNODE_QUERY = """
    MATCH (n:%s)-[r:HOMOLOG_OF]-(m:Human)
    WHERE  n.symbol = "%s"
    RETURN n.symbol AS symbol,
        n.sequence AS sequence,
        n.orf AS orf,
        n.length AS length,
        m.symbol AS human,
        r.blast_cov AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh AS nog_brh,
        r.pfam_sc AS pfam_sc,
        r.nog_eval AS nog_eval,
        r.blast_brh AS blast_brh,
        r.pfam_brh AS pfam_brh LIMIT 1
"""

PREDNODE_NOHOMOLOG_QUERY = """
    MATCH (n:%s)
    WHERE n.symbol = "%s"
    RETURN n.symbol   AS symbol,
           n.sequence AS sequence,
           n.orf      AS orf,
           n.length   AS length
"""

# ------------------------------------------------------------------------------
GET_CONNECTIONS_QUERY = """
    MATCH (n)-[r:INTERACT_WITH]-(m)
    WHERE n.symbol IN %s
    AND   m.symbol IN %s
    RETURN n.symbol      AS nsymbol,
           labels(n)     AS database,
           r.path_length AS path_length,
           r.int_prob    AS int_prob,
           r.dom_int_sc  AS dom_int_sc,
           r.cellcom_nto AS cellcom_nto,
           r.bioproc_nto AS bioproc_nto,
           r.molfun_nto  AS molfun_nto,
           m.symbol      AS msymbol
"""

GET_GENE = """
    MATCH (n:Smesgene)-[r:HAS_TRANSCRIPT]->(m:%s)
    WHERE m.symbol = '%s'
    RETURN n.symbol as genesymbol,
           n.name as name
"""

# ------------------------------------------------------------------------------
GO_QUERY = """
    MATCH (n:Go)
    WHERE n.accession = "%s"
    RETURN n.domain as domain, n.name as name
"""

# ------------------------------------------------------------------------------
GO_HUMAN_NODE_QUERY = """
    MATCH (n:Go)-[:HAS_GO]-(m:Human)
    WHERE n.accession = "%s"
    RETURN n.domain as domain, n.name as name, m.symbol as symbol
"""

# ------------------------------------------------------------------------------
GO_HUMAN_GET_GO_QUERY = """
    MATCH (n:Go)-[:HAS_GO]-(m:Human)
    WHERE m.symbol = "%s"
    RETURN n.accession as accession, n.domain as domain, n.name as name ORDER BY n.domain
"""


# ------------------------------------------------------------------------------
DOMAIN_TO_CONTIG = """
    MATCH (n:%s)-[:HAS_DOMAIN]->(m:Pfam)
    WHERE m.accession = "%s"
    RETURN n.symbol as symbol
"""

# ------------------------------------------------------------------------------
DOMAIN_TO_CONTIG_FUZZY = """
    MATCH (n:%s)-[:HAS_DOMAIN]->(m:Pfam)
    WHERE m.accession =~ "%s"
    RETURN n.symbol as symbol
"""

# ------------------------------------------------------------------------------
EXPERIMENT_QUERY = """
    MATCH (n:Experiment)
    WHERE n.id = "%s"
    RETURN
        n.id as identifier,
        n.maxexp as maxexp,
        n.minexp as minexp,
        n.reference as reference,
        n.url       as url,
        n.percentiles as percentiles
"""

# ------------------------------------------------------------------------------
ALL_EXPERIMENTS_QUERY = """
    MATCH (n:Experiment)-[r]-(m)
    RETURN distinct keys(r) as samples, n.id as identifier, n.url as url, toInt(n.private) as private, n.reference as reference, collect(distinct labels(m)) as datasets
"""

# ------------------------------------------------------------------------------
EXPRESSION_QUERY = """
    MATCH (n:%s)-[r:HAS_EXPRESSION]-(m:Experiment)
    WHERE n.symbol = "%s"
    AND m.id = "%s"
    RETURN r.%s as exp
"""

# ------------------------------------------------------------------------------
EXPRESSION_QUERY_GRAPH = """
    MATCH (n)-[r:HAS_EXPRESSION]-(m:Experiment)
    WHERE n.symbol IN %s
    AND m.id ="%s"
    RETURN n.symbol AS symbol, labels(n) AS database, r.%s AS exp
"""

# ------------------------------------------------------------------------------
HUMANNODE_QUERY = """
    MATCH (n:%s)
    WHERE n.symbol = "%s"
    RETURN n.symbol AS symbol
"""

# ------------------------------------------------------------------------------
PREDINTERACTION_QUERY = """
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)
    WHERE n.symbol = '%s' AND m.symbol = '%s'
    RETURN r.int_prob     AS int_prob,
           r.path_length  AS path_length,
           r.cellcom_nto  AS cellcom_nto,
           r.molfun_nto   AS molfun_nto,
           r.bioproc_nto  AS bioproc_nto,
           r.dom_int_sc   AS dom_int_sc
           LIMIT 1
"""

# ------------------------------------------------------------------------------
NEIGHBOURS_QUERY = """
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)-[s:HOMOLOG_OF]-(l:Human)
    WHERE  n.symbol = '%s'
    RETURN m.symbol         AS target,
           l.symbol         AS human,
           r.int_prob       AS int_prob,
           r.path_length    AS path_length,
           r.cellcom_nto    AS cellcom_nto,
           r.molfun_nto     AS molfun_nto,
           r.bioproc_nto    AS bioproc_nto,
           r.dom_int_sc     AS dom_int_sc,
           s.blast_cov      AS blast_cov,
           s.blast_eval     AS blast_eval,
           s.nog_brh        AS nog_brh,
           s.pfam_sc        AS pfam_sc,
           s.nog_eval       AS nog_eval,
           s.blast_brh      AS blast_brh,
           s.pfam_brh       AS pfam_brh
"""

# ------------------------------------------------------------------------------
NEIGHBOURS_QUERY_SHALLOW = """
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)-[s:HOMOLOG_OF]-(l:Human), (m)-[t:INTERACT_WITH*0..1]-(other)
    WHERE  n.symbol = '%s'
    RETURN m.symbol         AS target,
           count(t)         AS tdegree,
           l.symbol         AS human,
           r.int_prob       AS int_prob,
           r.path_length    AS path_length
"""

# ------------------------------------------------------------------------------
SYMBOL_WILDCARD = """
    MATCH (n:%s)
    WHERE n.symbol =~ "%s"
    RETURN n.symbol AS symbol
"""

# ------------------------------------------------------------------------------
NAME_WILDCARD = """
    MATCH (n:%s)
    WHERE n.name =~ "%s"
    RETURN n.symbol AS symbol
           n.name AS name
"""

# ------------------------------------------------------------------------------
PATH_QUERY = """
MATCH p=( (n:%s)-[r:INTERACT_WITH*%s]-(m:%s) )
WHERE n.symbol = '%s' AND m.symbol = '%s'
RETURN extract(nod IN nodes(p) | nod.symbol)                       AS symbols,
       extract(rel IN relationships(p) | toInt(rel.path_length))   AS path_length,
       extract(rel IN relationships(p) | toFloat(rel.int_prob))    AS int_prob
"""

# ------------------------------------------------------------------------------
DOMAIN_QUERY = """
    MATCH (n:%s)-[r]->(dom:Pfam)
    WHERE n.symbol = '%s'
    RETURN dom.accession   AS accession,
           dom.description AS description,
           dom.identifier  AS identifier,
           dom.mlength     AS mlength,
           r.pfam_start    AS p_start,
           r.pfam_end      AS p_end,
           r.s_start       AS s_start,
           r.s_end         AS s_end,
           r.perc          AS perc
"""

# ------------------------------------------------------------------------------
OFFSYMBOL_QUERY = """
    MATCH (n:OFF_SYMBOL)<-[r]-(m:%s)
    WHERE n.symbol = '%s'
    RETURN m.symbol AS symbol
"""

# ------------------------------------------------------------------------------
HOMOLOGS_QUERY = """
    MATCH (n:Human)-[r:HOMOLOG_OF]-(m:%s)
    WHERE  n.symbol = "%s"
    RETURN n.symbol  AS human,
        m.symbol     AS homolog,
        r.blast_cov  AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh    AS nog_brh,
        r.pfam_sc    AS pfam_sc,
        r.nog_eval   AS nog_eval,
        r.blast_brh  AS blast_brh,
        r.pfam_brh   AS pfam_brh,
        labels(m)    AS database
"""


# ------------------------------------------------------------------------------
HOMOLOGS_QUERY_ALL = """
    MATCH (n:Human)-[r:HOMOLOG_OF]-(m)
    WHERE  n.symbol = "%s"
    RETURN n.symbol  AS human,
        m.symbol     AS homolog,
        r.blast_cov  AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh    AS nog_brh,
        r.pfam_sc    AS pfam_sc,
        r.nog_eval   AS nog_eval,
        r.blast_brh  AS blast_brh,
        r.pfam_brh   AS pfam_brh,
        labels(m)    AS database
"""

# ------------------------------------------------------------------------------
SUMMARY_QUERY = """
    MATCH (n:Human)
    WHERE n.symbol = "%s"
    RETURN n.summary as summary,
           n.summary_source as summary_source
"""

# ------------------------------------------------------------------------------
GET_GENES_QUERY = """
    MATCH (n:Smesgene)-[r:HAS_TRANSCRIPT]->(m:%s)
    WHERE m.symbol = "%s"
    RETURN n.symbol as symbol,
           n.name as name,
           n.start as start,
           n.end as end,
           n.sequence as sequence,
           n.strand as strand
"""

# ------------------------------------------------------------------------------
GET_GENES_FROMHUMAN_QUERY = """
    MATCH (n:Human)<-[r:HOMOLOG_OF]-(m:%s)<-[s:HAS_TRANSCRIPT]-(l:Smesgene)
    WHERE n.symbol = "%s"
    RETURN l.symbol     AS symbol,
           l.name       AS name,
           l.start      AS start,
           l.end        AS end,
           l.sequence   AS sequence,
           l.strand     AS strand,
           m.symbol     AS prednode_symbol,
           r.blast_cov  AS blast_cov,
           r.blast_eval AS blast_eval,
           r.nog_brh    AS nog_brh,
           r.pfam_sc    AS pfam_sc,
           r.nog_eval   AS nog_eval,
           r.blast_brh  AS blast_brh,
           r.pfam_brh   AS pfam_brh
"""

SMESGENE_QUERY = """
    MATCH (n:Smesgene)
    WHERE n.symbol = "%s"
    RETURN n.symbol as symbol,
           n.name as name,
           n.start as start,
           n.end as end,
           n.sequence as sequence,
           n.chromosome as chromosome,
           n.strand as strand
"""

SMESGENE_GET_CONTIGS_QUERY = """
    MATCH (n:Smesgene)-[r:HAS_TRANSCRIPT]->(m:%s)
    WHERE  n.symbol = "%s"
    RETURN m.symbol as symbol,
           m.length as length
    ORDER BY m.length DESC
"""

SMESGENE_GET_ALL_CONTIGS_QUERY = """
    MATCH (n:Smesgene)-[r:HAS_TRANSCRIPT]->(m)
    WHERE  n.symbol = "%s"
    RETURN labels(m) as database,
           m.symbol as symbol,
           m.length as length
    ORDER BY labels(m), m.length DESC
"""

GO_TO_CONTIG = """
    MATCH (go:Go)<-[r:HAS_GO]-(h:Human)<-[hom:HOMOLOG_OF]-(c:%s)
    WHERE go.accession = "%s"
    RETURN c.symbol AS symbol,
           h.symbol AS human,
           hom.blast_cov  AS blast_cov,
           hom.blast_eval AS blast_eval,
           hom.nog_brh    AS nog_brh,
           hom.pfam_sc    AS pfam_sc,
           hom.nog_eval   AS nog_eval,
           hom.blast_brh  AS blast_brh,
           hom.pfam_brh   AS pfam_brh
"""