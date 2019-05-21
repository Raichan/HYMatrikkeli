# -*- coding: UTF-8 -*-

from rdflib import Namespace, URIRef, Graph, Literal, XSD
from rdflib.namespace import RDF, FOAF, SKOS
import re
import csv
import CSVtoRDFhelpers

owl = Namespace("http://www.w3.org/2002/07/owl#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
schema = Namespace("http://schema.org/")
xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
dct = Namespace("http://purl.org/dc/terms/")
bioc = Namespace("http://ldf.fi/schema/bioc/")
pr = Namespace("http://ldf.fi/schema/person_registry/")
ns1 = Namespace("http://ldf.fi/yomatrikkeli/")

refUrl = "https://ylioppilasmatrikkeli.helsinki.fi/henkilo.php?id="

g = Graph()
rowno = 0
notfound = 0

with open(r"C:\Users\Laura\Documents\Norssin matrikkeli data\Extension.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter =',')
    for row in reader:
        rowno = rowno + 1
        
        if(rowno == 1): # skip first row, TODO use all rows
            continue

        rowid = row[0]
        name = row[4] + " " + row[3]
        entry = row[6]
        
        if not name: # Skip rows with empty data
            continue

        person = URIRef("http://ldf.fi/yomatrikkeli/p" + str(rowid))
        g.add( (URIRef(person), RDF.type , FOAF.Person) )
        g.add( (URIRef(person), pr.entryText , Literal(entry, lang='fi') ) )
        g.add( (URIRef(person), ns1.id , Literal(rowid) ) )
        
        givenname = row[4]
        familyname = row[3]

        g.add( (URIRef(person), schema.givenName , Literal(givenname, lang='fi') ) )
        g.add( (URIRef(person), schema.familyName , Literal(familyname, lang='fi') ) )
        
        splitentry = entry.split(". ")
        
        # enrollment year
        eYear = row[1]
        g.add( (URIRef(person), ns1.enrollmentYear, Literal(eYear, datatype=XSD.year) ) ) # TODO mita eroa on year ja gYear, pitaisiko olla year
        
        # Find birth and death info
        birth = re.search('((.*?) ([0123]?[0-9])\.([0123]?[0-9])\.(1[0-9]{3}))', entry)
        if(birth and not "†" in birth.group(2)):
            bYear = birth.group(5)
            bdstring = birth.group(5) + "-" + CSVtoRDFhelpers.date_with_zeros(birth.group(4)) + "-" + CSVtoRDFhelpers.date_with_zeros(birth.group(3)) # yyyy-MM-dd
            bPlace = birth.group(2)
            g.add( (URIRef(person), schema.birthDate , Literal(bdstring, datatype=XSD.date) ) )
            g.add( (URIRef(person), schema.birthPlace , Literal(bPlace, lang='fi') ) )

        death = re.search('(†(.*?) ([0123]?[0-9])\.([0123]?[0-9])\.(1[0-9]{3}))', entry)
        if(death):
            dYear = death.group(5)
            ddstring = death.group(5) + "-" + CSVtoRDFhelpers.date_with_zeros(death.group(4)) + "-" + CSVtoRDFhelpers.date_with_zeros(death.group(3)) # yyyy-MM-dd
            dPlace = death.group(2).strip()
            g.add( (URIRef(person), schema.deathPlace , Literal(dPlace, lang='fi') ) )
            g.add( (URIRef(person), schema.deathDate , Literal(ddstring, datatype=XSD.date) ) )

        spouse = re.search('(– Pso (1\) )?(1[0-9]{3} )?(.*?)(\.|,))', entry)
        if(spouse):
            spousefound = spouse.group(1)
            spousename = spouse.group(4)
            if("1)" in spousefound):
                spousename = "1. " + spousename
                spouse2 = re.search('(– Pso (1\) )?(1[0-9]{3} )?(.*?)(\.|,).*?2\) (1[0-9]{3} )?(.*?)(\.|,))', entry)
                if(spouse2):
                    spousename2 = "2. " + spouse2.group(7)
                    g.add( (URIRef(person), pr.spouse , Literal(spousename2, lang='fi') ) )
            g.add( (URIRef(person), pr.spouse , Literal(spousename, lang='fi') ) )
        
        relatedLink = URIRef("https://ylioppilasmatrikkeli.helsinki.fi/henkilo.php?id=" + rowid)
        g.add( (URIRef(person), schema.relatedLink , URIRef(relatedLink) ) )

        prefLabel = name + " (" + (bYear or "?") + "-" + (dYear or "?") + ")"
        g.add( (URIRef(person), SKOS.prefLabel , Literal(prefLabel, lang='fi') ) )
        
        g.add( (URIRef(person), dct.source , ns1.yo1853 ) )

# create prefixes
g.bind("owl", owl)
g.bind("rdf", rdf)
g.bind("rdfs", rdfs)
g.bind("schema", schema)
g.bind("xsd", xsd)
g.bind("dct", dct)
g.bind("bioc", bioc)
g.bind("person_registry", pr)
g.bind("ns1", ns1)

g.serialize(destination='yomatrikkeli53.ttl', format='turtle')