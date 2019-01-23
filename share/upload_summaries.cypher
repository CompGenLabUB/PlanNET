LOAD CSV WITH HEADERS FROM "file:///summary.clean.csv" AS row
MATCH (n:Human)
WHERE n.symbol = row.gene
SET n.summary = row.summary
SET n.summary_source = row.summary_source
