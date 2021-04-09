    ## Beacon "Handovers"

    Beacon `handover` objects represent an efficient and - if used properly -
    privacy protecting mechanism to enable data delivery, in conjunction with
    Beacon queries.

    The advantages of using the "handover" mechanism lie especially in:

    * the separation of the standard Beacon variant query and response with the privacy-protecting
    response, limited to yes/no/count, from meta-information about individuals and
    biosamples
    * the power to link to any type of data delivery protocol for "documents"
    (i.e. database records) related to the Beacon query matches

    Handled in a controled/protected environment one could in pprinciple use e.g.
    the `handover` protocol to access the electronic health records (EHR) of patients
    for which a specific genomic variantr query resulte din a match, to follow up 
    on thiose patients' history & progress, or to initiate interventions based on
    accuing evidence related to the matched variant(s).

    While the `handover` mechanisms is powerful through its flexibility, an obvious
    disadvantage lies in the lack of control about the implemented mechanisms. A
    good siolution here would be to provide some prototype designs, e.g. "Phenopackets"
    formatted delivery of "bio" data.

