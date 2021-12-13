#!/bin/bash

# Script to ensure MongoDB indexing
# Please modify for additional collections and changing attributes.

#
# progenetix publications
#
for field in \"id\" \"provenance.geo.city\" \"counts.ccgh\" \"counts.acgh\" \"counts.wes\" \"counts.wgs\" \"counts.ngs\" \"counts.genomes\" \"external_references.type.id\"
do
  mongo progenetix --eval "db.publications.createIndex( { $field : 1 } )"
done

#
# progenetix genes
#
for field in symbol reference_name start end gene_id swiss_prot_accessions
do
  mongo progenetix --eval "db.genes.createIndex( { $field : 1 } )"
done


for db in progenetix 1000genomesDRAGEN cellosaurus
do
    for dbcoll in biosamples callsets individuals collations
	do
		echo "=> index for $db.$dbcoll.id"
		mongo $db --eval "db.$dbcoll.createIndex( { 'id' : 1 }, { 'unique': true } )"

		for field in variant_type reference_bases reference_name callset_id alternate_bases individual_id biosample_id start \"end\" \"info.var_length\" variant_internal_id
		do
			echo "=> index for $db.variants.$field"
			mongo $db --eval "db.variants.createIndex( { $field : 1 } )"
		done
	
		for field in \"external_references.id\" \"external_references.description\" description \"provenance.geo_location.properties.city\" \"provenance.geo_location.properties.country\" individual_id age_at_collection biosample_status.id
		do
			echo "=> index for $db.biosamples.$field"
			mongo $db --eval "db.biosamples.createIndex( { $field : 1 } )"
		done
	
		for field in \"provenance.geo_location.properties.city\" \"provenance.geo_location.properties.country\" biosample_id individual_id
		do
			echo "=> index for $db.callsets.$field"
			mongo $db --eval "db.callsets.createIndex( { $field : 1 } )"
		done
	
	done
	
    for dbcoll in collations
	do
		for field in child_terms id label count collation_type prefix
		do
			echo "=> index for $db.collations.$field"
			mongo $db --eval "db.collations.createIndex( { $field : 1 } )"
		done	
	done

	for dbcoll in biosamples individuals callsets
	do
		echo "=> index for $db.$dbcoll.provenance.geo_location.geometry"
		mongo $db --eval "db.$dbcoll.createIndex( { \"provenance.geo_location.geometry\" : \"2dsphere\" } )"
	done
done

	
for db in progenetix 1000genomesDRAGEN cellosaurus
do
	for dbcoll in biosamples
	do
		echo "=> index for $db.$dbcoll histologies etc."
		for field in \"histological_diagnosis.id\" \"sampled_tissue.id\" \"icdo_morphology.id\" \"icdo_topography.id\" \"pathological_tnm_findings.id\" \"tumor_grade.id\" \"pathological_stage.id\"
		do
			echo "=> index for $db.$dbcoll.$field"
			mongo $db --eval "db.$dbcoll.createIndex( { $field : 1 } )"
		done
	done
done

for db in progenetix
do
    for dbcoll in publications
    do
        echo "=> index for $db.$dbcoll.provenance.geo_location.geometry"
        mongo $db --eval "db.$dbcoll.createIndex( { \"provenance.geo_location.geometry\" : \"2dsphere\" } )"
    done
done


