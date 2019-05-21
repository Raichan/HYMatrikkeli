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

with open(r"C:\Users\Laura\Documents\Norssin matrikkeli data\HakemistoDescriptions.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter ='\t')
    for row in reader:
        rowno = rowno + 1

        if(rowno == 1):
            continue
        
        rowid = row[1]
        name = row[4]
        entry = row[5]
        
        person = URIRef("http://ldf.fi/yomatrikkeli/p" + str(rowid))
        g.add( (URIRef(person), RDF.type , FOAF.Person) )
        
        if not name: # Duplicate entry or extra row
            if("Rehtori" not in entry and "Merkintä" not in entry and "Viittauksia" not in entry):
                sameid = re.search('(>(.*)<\/a>)', entry)
                if(sameid):
                    samePerson = URIRef("http://ldf.fi/yomatrikkeli/p" + str(sameid.group(2)))
                    g.add( (URIRef(person), owl.sameAs , samePerson) )
            continue

        g.add( (URIRef(person), pr.entryText , Literal(entry, lang='fi') ) )
        g.add( (URIRef(person), ns1.id , Literal(rowid) ) )
        
        givenname = ""
        familyname = ""
        if name:
            n = re.search('\((.+?)\)', name)
            # special cases like "Abraham (Abrahamus Henrici)"
            if n:
                foundname = n.group(1)
                namesplit = foundname.rsplit(' ', 1)
                givenname = namesplit[0]
                if(len(namesplit) > 1):
                    familyname = foundname.split(' ')[-1]
            # names in default format
            else:
                vonfind = re.search('((.*) ((von|af|de|de la|von der|In de) .*))', name)
                if(vonfind):
                    givenname = vonfind.group(2)
                    familyname = vonfind.group(3)
                # special case for unclear family names
                elif (" tai " in name):
                    namesplit = name.split(' ', 1)
                    givenname = namesplit[0]
                    familyname = namesplit[1]
                # no special circumstances
                else:
                    namesplit = name.rsplit(' ', 1)
                    givenname = namesplit[0]
                    if(len(namesplit) > 1):
                        familyname = name.split(' ')[-1]

            if givenname:
                g.add( (URIRef(person), schema.givenName , Literal(givenname, lang='fi') ) )
            if familyname:
                g.add( (URIRef(person), schema.familyName , Literal(familyname, lang='fi') ) )
        
        splitentry = entry.split(". ")
        
        enrollmentsplit = entry.split("<")[0]
        enrollmentyear = re.search('(1[0-9]{3})', enrollmentsplit) # Find year in string
        if(enrollmentyear):
            eYear = enrollmentyear.group(1)
            g.add( (URIRef(person), ns1.enrollmentYear, Literal(eYear, datatype=XSD.year) ) ) # TODO mita eroa on year ja gYear, pitaisiko olla year
        
        # Find birth and death info
        bDay = ""
        bMonth = ""
        bYear = ""
        bPlace = ""
        dDay = ""
        dMonth = ""
        dYear = ""
        dPlace = ""
        
        birthstring = re.search('(\*(?![^(]*\)) (.*?)((([0123]?[0-9])\.)?(([0123]?[0-9])\.)?(1[0-9]{3})))', entry)
        #birthstring = re.search('(\*(?![^(]*\)) (.*?(ssa|ssä|lla|llä|noin|a.n.|a.u.|\(?\)))??.*?((([0123]?[0-9])\.)?(([0123]?[0-9])\.)?(1[0-9]{3})))', entry)
        if(birthstring):
            bDay = birthstring.group(5) or None
            bMonth = birthstring.group(7) or None
            bYear = birthstring.group(8)
            
            if(bDay and bMonth and bYear):
                bdstring = bYear + "-" + CSVtoRDFhelpers.date_with_zeros(bMonth) + "-" + CSVtoRDFhelpers.date_with_zeros(bDay) # yyyy-MM-dd
                g.add( (URIRef(person), schema.birthDate , Literal(bdstring, datatype=XSD.date) ) )
            elif(bDay and bYear):
                bMonth = bDay
                bDay = "01"
                bdstring = bYear + "-" + CSVtoRDFhelpers.date_with_zeros(bMonth) + "-" + bDay # yyyy-MM-dd
                g.add( (URIRef(person), schema.birthDate , Literal(bdstring, datatype=XSD.date) ) )
            elif(bYear):
                g.add( (URIRef(person), schema.birthDate , Literal(bYear, datatype=XSD.year) ) )
            
            if(birthstring.group(2)):
                bPlace = birthstring.group(2)
                removelist = ["noin", "kaksosena", "postuumina", "luultavasti", "luult.", "mahdollisesti", "mahd.", "ehkä", "viimeistään", "a.n.", "a.u.", "Ol.", "Vl.", "v.l.", "Ul.", "u.l.", "Tl.", "Hl.", "~", "kastettu", ",", "(?)"]
                for word in list(removelist):  # iterating on a copy since removing will mess things up
                    if word in bPlace:
                        bPlace = bPlace.replace(word, "")
                
                bPlace = bPlace.split('(')[0]
                bPlace = bPlace.split('.')[0]
                bPlace = bPlace.strip()
                if (len(bPlace) > 0):
                    g.add( (URIRef(person), schema.birthPlace , Literal(bPlace, lang='fi') ) )
        
        # birth place special case
        if bPlace == "":
            for e in splitentry:
                if e.startswith("Kotoisin"):
                    bPlace = e.split(' ', 1)[1]
                    g.add( (URIRef(person), schema.birthPlace , Literal(bPlace, lang='fi') ) )
                    break
        
        deathstring = re.search('(†(?![^(]*\)) (.*?)((([0123]?[0-9])\.)?(([0123]?[0-9])\.)?(1[0-9]{3})))', entry)
        #deathstring = re.search('(†(?![^(]*\)) ([a-zA-ZäÄöÖåÅ]*?(ssa|ssä|lla|llä|noin)) ((([0123]?[0-9])\.)?(([0123]?[0-9])\.)?(1[0-9]{3})))', entry)
        if(deathstring):
            dDay = deathstring.group(5) or None
            dMonth = deathstring.group(7) or None
            dYear = deathstring.group(8)
            
            if(dDay and dMonth and dYear):
                ddstring = dYear + "-" + CSVtoRDFhelpers.date_with_zeros(dMonth) + "-" + CSVtoRDFhelpers.date_with_zeros(dDay) # yyyy-MM-dd
                g.add( (URIRef(person), schema.deathDate , Literal(ddstring, datatype=XSD.date) ) )
            elif(dDay and dYear):
                dMonth = dDay
                dDay = "01"
                ddstring = dYear + "-" + CSVtoRDFhelpers.date_with_zeros(dMonth) + "-" + dDay # yyyy-MM-dd
                g.add( (URIRef(person), schema.deathDate , Literal(ddstring, datatype=XSD.date) ) )
            elif(dYear):
                ddstring = dYear
                g.add( (URIRef(person), schema.deathDate , Literal(dYear, datatype=XSD.year) ) )
            
            if(deathstring.group(2)):
                dPlace = deathstring.group(2)
                removelist = ["entisenä", "ylioppilaana", "nuorena", "hukkui", "kaatui", "noin", "luult", "ehkä", "Tl", "Vl.", "Vl", "Ul", "u.l.", "Ol", "(?)"]
                for word in list(removelist):  # iterating on a copy since removing will mess things up
                    if word in dPlace:
                        dPlace = dPlace.replace(word, "")
                
                if not (dPlace.startswith("(") and len(dPlace) > 1):
                    dPlace = dPlace.split('(')[0]
                dPlace = dPlace.split('.')[0]
                dPlace = dPlace.strip()
                g.add( (URIRef(person), schema.birthPlace , Literal(bPlace, lang='fi') ) )
        
        spouse = re.search('(Pso:.*?<em>(.*?)<\/em>.*?)', entry)
        if(spouse):
            spousename = spouse.group(2)
            if "1:o" in spouse.group(1): # find 2nd wife
                spousename = "1. "+ spousename
                spouse2 = re.search('(Pso:.*?<em>(.*?)<\/em>.*?2:o.*?<em>(.*?)<\/em>)', entry)
                if(spouse2):
                    spousename2 = "2. " + spouse2.group(3)
                    g.add( (URIRef(person), pr.spouse , Literal(spousename2, lang='fi') ) )
            g.add( (URIRef(person), pr.spouse , Literal(spousename, lang='fi') ) )
            
        relatives = re.findall('(\\<p>(.*?): (.*?) <em>(.*?)<\/em>(.*?)">(.*?)<\/a>)', entry)
        for r in relatives:
            rel = r[1] + " " + r[3] + " " + r[5]
            g.add( (URIRef(person), pr.relatedYo , Literal(rel, lang='fi') ) )
                
        relatedLink = URIRef("https://ylioppilasmatrikkeli.helsinki.fi/henkilo.php?id=" + rowid)
        g.add( (URIRef(person), schema.relatedLink , URIRef(relatedLink) ) )

        prefLabel = name + " (" + (bYear or "?") + "-" + (dYear or "?") + ")"
        g.add( (URIRef(person), SKOS.prefLabel , Literal(prefLabel, lang='fi') ) )
        
        g.add( (URIRef(person), dct.source , ns1.yo1640_1852 ) )
        
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

g.serialize(destination='yomatrikkeli.ttl', format='turtle')