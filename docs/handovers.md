    ## Beacon "Handovers"

    Beacon `handover` objects represent an efficient and - used properly -
    privacy protecting mechanism to enable data delivery, in conjunction with
    Beacon queries.

    The advantages of using the "handover" mechanism lie especially in:

    * the separation of the standard Beacon variant query and response with the
      privacy-protecting boolean or count response from record level details
    * the possibility to link non-Beacon data delivery protocols for "documents"
      (e.g. database records, files)

    Handled in a controled/protected environment one could in principle use
    the `handover` protocol to access the electronic health records (EHR) of
    patients matching a Beacon request.

    While the `handover` mechanisms is powerful through its flexibility, an
    obvious disadvantage lies in the lack of control about the implemented mechanisms.