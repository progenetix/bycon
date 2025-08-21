"""Translates various external formats into VRS models.

Input formats: VRS (serialized), hgvs, spdi, gnomad (vcf), beacon
Output formats: VRS (serialized), hgvs, spdi, gnomad (vcf)

"""

import logging
import re
from abc import ABC
from collections.abc import Mapping
from typing import Protocol

from ga4gh.core import ga4gh_identify
from ga4gh.vrs import models, normalize
from ga4gh.vrs.dataproxy import SequenceProxy, _DataProxy
from ga4gh.vrs.extras.decorators import lazy_property
from ga4gh.vrs.normalize import denormalize_reference_length_expression

_logger = logging.getLogger(__name__)


class VariationToStrProtocol(Protocol):
    """Protocol for translating VRS objects to other string expressions.

    This protocol defines a callable interface for translating a VRS object
    into variation strings, with optional keyword arguments for customization.
    """

    def __call__(self, vo: models._VariationBase, **kwargs) -> list[str]:
        """Translate vrs object `vo` to variation string expressions"""


class VariationFromStrProtocol(Protocol):
    """Protocol for translating variation strings to VRS objects.

    This protocol defines a callable interface for translating a variation
    string into a VRS object, with optional keyword arguments for customization.
    """

    def __call__(self, expr: str, **kwargs) -> models._VariationBase | None:
        """Translate variation string `expr` to a VRS object"""


class _Translator(ABC):  # noqa: B024
    """abstract class / interface for VRS to/from translation needs

     Translates various variation formats to and from GA4GH VRS models

    All `from_` methods follow this pattern:
    * If the argument does not appear to be an appropriate type, None is returned
    * Otherwise, the argument is expected to be of the correct type.  If an error occurs during processing,
      an exception is raised.
    * Otherwise, the VRS object is returned

    """

    gnomad_re = re.compile(
        r"(?P<chr>[^-]+)-(?P<pos>\d+)-(?P<ref>[ACGTURYKMSWBDHVN]+)-(?P<alt>[ACGTURYKMSWBDHVN]+)",
        re.IGNORECASE,
    )
    spdi_re = re.compile(
        r"(?P<ac>[^:]+):(?P<pos>\d+):(?P<del_len_or_seq>\w*):(?P<ins_seq>\w*)"
    )
    pgxseg_re = re.compile(
        r"""
        (?P<biosample_id>[^:]+)((?:::)|\t)
        (?P<reference_name>[\w:]+)(?:\2)
        (?P<start>\d+)(?:\2)
        (?P<end>\d+)(?:\2)
        (?P<value>[^\s]*)(?:\2)
        (?P<variant_type>[\w]*)(?:\2)
        (?P<reference_sequence>[\.ACGTN]*)(?:\2)
        (?P<sequence>[\.ACGTN]*)(?:\2)
        (?:
            (?P<variant_state_id>[\w:]*)(?:\2)
            (?P<variant_state_label>[\w\- ]*)
            ((?:\2)(?P<other>.*))?
        )?        
        """, re.X)

    pgxadjoined_re = re.compile(
        r"""
        (?P<adj_seqid_1>(?:refseq:)?[\w\.]+)::
        (?P<pos_type_1>\w+)::
        (?P<range_1>\d+,\d+)&&
        (?P<adj_seqid_2>(?:refseq:)?[\w\.]+)::
        (?P<pos_type_2>\w+)::
        (?P<range_2>\d+,\d+)
        (::(?P<other>.*))?
        """, re.X)

    def __init__(
        self,
        data_proxy: _DataProxy,
        default_assembly_name: str = "GRCh38",
        identify: bool = True,
        rle_seq_limit: int | None = 50,
    ):
        self.default_assembly_name = default_assembly_name
        self.data_proxy = data_proxy
        self.identify = identify
        self.rle_seq_limit = rle_seq_limit
        self.from_translators: dict[str, VariationFromStrProtocol] = {}
        self.to_translators: dict[str, VariationToStrProtocol] = {}

    def translate_from(
        self, var: str, fmt: str | None = None, **kwargs
    ) -> models._VariationBase:
        """Translate variation `var` to VRS object

        If `fmt` is None, guess the appropriate format and return the variant.
        If `fmt` is specified, try only that format.

        See also notes about `from_` and `to_` methods.

        kwargs:
            For CnvTranslator
                copies(int): The number of copies to use. If provided will return a
                    CopyNumberCount
                copy_change(models.CopyChange): Copy change. If not provided, default is
                    EFO:0030067 for deletions and EFO:0030070 for duplications
            For AlleleTranslator
                assembly_name (str): Assembly used for `var`. Defaults to the
                    `default_assembly_name`. Only used for beacon and gnomad.
                require_validation (bool): If `True` then validation checks must pass in
                    order to return a VRS object. A `DataProxyValidationError` will be
                    raised if validation checks fail. If `False` then VRS object will be
                    returned even if validation checks fail. Defaults to `True`.
                rle_seq_limit Optional(int): If RLE is set as the new state after
                    normalization, this sets the limit for the length of the `sequence`.
                    To exclude `sequence` from the response, set to 0.
                    For no limit, set to `None`.
                    Defaults value set in instance variable, `rle_seq_limit`.
                do_normalize (bool): `True` if fully justified normalization should be
                    performed. `False` otherwise. Defaults to `True`
        """
        if fmt:
            try:
                t = self.from_translators[fmt]
            except KeyError as e:
                msg = f"{fmt} is not supported"
                raise NotImplementedError(msg) from e
            else:
                o = t(var, **kwargs)
                if o is None:
                    msg = f"Unable to parse data as {fmt} variation"
                    raise ValueError(msg)
                return o

        for t in self.from_translators.values():
            o = t(var, **kwargs)
            if o:
                return o

        formats = list(self.from_translators.keys())
        msg = f"Unable to parse data as {', '.join(formats)}"
        raise ValueError(msg)

    def translate_to(self, vo: models._VariationBase, fmt: str, **kwargs) -> list[str]:
        """Translate vrs object `vo` to named format `fmt`

        kwargs:
            ref_seq_limit Optional(int):
                If vo.state is a ReferenceLengthExpression, and `ref_seq_limit` is specified, and `fmt` is `spdi`, the reference sequence is included in the SPDI expression if it is below the limit Otherwise only the length of the reference sequence is included. If the limit is None, the reference sequence is always included. In all cases, the alt sequence is included. Default is 0 (never include reference sequence).
        """
        t = self.to_translators[fmt]
        return t(vo, **kwargs)

    ############################################################################
    # INTERNAL


class AlleleTranslator(_Translator):
    """Class for translating formats to and from VRS Alleles"""

    def __init__(
        self,
        data_proxy: _DataProxy,
        default_assembly_name: str = "GRCh38",
        identify: bool = True,
    ):
        """Initialize AlleleTranslator class"""
        super().__init__(data_proxy, default_assembly_name, identify)

        self.from_translators = {
            "gnomad": self._from_gnomad,
            "pgxseg": self._from_pgxseg
        }

        self.to_translators = {
            "spdi": self._to_spdi
        }

    def _create_allele(self, values: dict, **kwargs) -> models.Allele:
        """Create an allele object with the given parameters.

        Args:
            values (dict): The values to use for creating the allele object.
                'refget_accession' (str): The accession ID of the reference genome.
                'start' (int): The start position of the allele.
                'end' (int): The end position of the allele.
                literal_sequence' (str): The literal sequence for the allele.
            **kwargs: Additional keyword arguments.

        Returns:
            models.Allele: The created allele object.

        """
        seq_ref = models.SequenceReference(refgetAccession=values["refget_accession"])
        location = models.SequenceLocation(
            sequenceReference=seq_ref, start=values["start"], end=values["end"]
        )
        state = models.LiteralSequenceExpression(sequence=values["literal_sequence"])
        allele = models.Allele(location=location, state=state)
        return self._post_process_imported_allele(allele, **kwargs)


    def _from_gnomad(self, gnomad_expr: str, **kwargs) -> models.Allele | None:
        """Parse gnomAD-style VCF expression into VRS Allele

        kwargs:
            assembly_name (str): Assembly used for `gnomad_expr`.
            require_validation (bool): If `True` then validation checks must pass in
                order to return a VRS object. A `DataProxyValidationError` will be
                raised if validation checks fail. If `False` then VRS object will be
                returned even if validation checks fail. Defaults to `True`.
            rle_seq_limit Optional(int): If RLE is set as the new state after
                normalization, this sets the limit for the length of the `sequence`.
                To exclude `sequence` from the response, set to 0.
                For no limit, set to `None`.
                Defaults value set in instance variable, `rle_seq_limit`.
            do_normalize (bool): `True` if fully justified normalization should be
                performed. `False` otherwise. Defaults to `True`

        #>>> a = tlr.from_gnomad("1-55516888-G-GA")
        #>>> a.model_dump()
        {
          'location': {
            'end': 55516888,
            'start': 55516887,
            'sequenceReference': {
              'refgetAccession': 'SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO',
              'type': 'SequenceReference'
            },
            'type': 'SequenceLocation'
          },
          'state': {
            'sequence': 'GA',
            'type': 'LiteralSequenceExpression'
          },
          'type': 'Allele'
        }

        """
        if not isinstance(gnomad_expr, str):
            return None
        m = self.gnomad_re.match(gnomad_expr)
        if not m:
            return None

        g = m.groupdict()
        assembly_name = kwargs.get("assembly_name", self.default_assembly_name)
        sequence = assembly_name + ":" + g["chr"]
        refget_accession = self.data_proxy.derive_refget_accession(sequence)
        if not refget_accession:
            return None

        start = int(g["pos"]) - 1
        ref = g["ref"].upper()
        alt = g["alt"].upper()
        end = start + len(ref)
        ins_seq = alt

        # validation checks
        self.data_proxy.validate_ref_seq(
            sequence,
            start,
            end,
            ref,
            require_validation=kwargs.get("require_validation", True),
        )

        values = {
            "refget_accession": refget_accession,
            "start": start,
            "end": end,
            "literal_sequence": ins_seq,
        }
        return self._create_allele(values, **kwargs)

    def _from_pgxseg(self, pgxseg: str, **kwargs) -> models.Allele | None:
        """Parse pgxseg string (line) in to a GA4GH Allele

        This is based on the SPDI conversion, adjusted for the pgxseg format.

        kwargs:
            rle_seq_limit Optional(int): If RLE is set as the new state after
                normalization, this sets the limit for the length of the `sequence`.
                To exclude `sequence` from the response, set to 0.
                For no limit, set to `None`.
                Defaults value set in instance variable, `rle_seq_limit`.
            do_normalize (bool): `True` if fully justified normalization should be
                performed. `False` otherwise. Defaults to `True`

        #>>> a = tlr.from_spdi("pgxbs-kl8heu35::4::153259034::153259035::::SNV::A::T::SO:0001059::sequence_alteration")
        #>>> a.model_dump()
        {
          'location': {
            'end': 32936732,
            'start': 32936731,
            'sequenceReference': {
                'refgetAccession': 'SQ._0wi-qoDrvram155UmcSC-zA5ZK4fpLT',
                'type': 'SequenceReference'
            },
            'type': 'SequenceLocation'
          },
          'state': {
              'sequence': 'C',
              'type': 'LiteralSequenceExpression'
          },
          'type': 'Allele'
        }
        """
        if not isinstance(pgxseg, str):
            return None

        m = self.pgxseg_re.match(pgxseg)
        if not m:
            return None
        g = m.groupdict()

        reference_name = g.get("reference_name", "___unknown___")
        if not ":" in reference_name:
            reference_name = f"{self.default_assembly_name}:{reference_name}"
        refget_accession = self.data_proxy.derive_refget_accession(reference_name)
        if not refget_accession:
            return None

        start = int(g["start"])
        del_seq = g.get("reference_sequence", "").replace(".", "")
        del_len = len(del_seq)
        end = g.get("end", start + del_len)

        values = {
            "refget_accession": refget_accession,
            "start": start,
            "end": end,
            "literal_sequence": g.get("sequence", "").replace(".", ""),
        }

        return self._create_allele(values, **kwargs)

    def _to_spdi(
        self, vo: models.Allele, namespace: str | None = "refseq", **kwargs
    ) -> list[str]:
        """Generate a *list* of SPDI expressions for VRS Allele.

        If `namespace` is not None, returns SPDI strings for the
        specified namespace.

        If `namespace` is None, returns SPDI strings for all alias
        translations.

        If `ref_seq_limit` is specified, the reference sequence is
        included in the SPDI expression only if it is below the limit.
        Otherwise only the length of the reference sequence is
        included. If the limit is None, the reference sequence is
        always included. In all cases, the alt sequence is included.
        Default is 0 (never include reference sequence).

        If no alias translations are available, an empty list is
        returned.

        If the VRS object cannot be expressed as SPDI, raises ValueError.

        SPDI and VRS use identical normalization. The incoming Allele
        is expected to be normalized per VRS spec.
        """
        sequence = f"ga4gh:{vo.location.get_refget_accession()}"
        aliases = self.data_proxy.translate_sequence_identifier(sequence, namespace)
        aliases = [a.split(":")[1] for a in aliases]
        seq_proxies = {a: SequenceProxy(self.data_proxy, a) for a in aliases}
        start, end = vo.location.start, vo.location.end
        spdi_exprs = []

        for alias in aliases:
            # Get the reference sequence
            seq_proxy = seq_proxies[alias]
            ref_seq = seq_proxy[start:end]

            if vo.state.type == models.VrsType.REF_LEN_EXPR.value:
                # Derived from reference. sequence included if under limit, but
                # we can derive it again from the reference.
                alt_seq = denormalize_reference_length_expression(
                    ref_seq=ref_seq,
                    repeat_subunit_length=vo.state.repeatSubunitLength,
                    alt_length=vo.state.length,
                )
                # Warn if the derived sequence is different from the one in the object
                if vo.state.sequence and vo.state.sequence.root != alt_seq:
                    _logger.warning(
                        "Derived sequence '%s' is different from provided state.sequence '%s'",
                        alt_seq,
                        vo.state.sequence.root,
                    )
            else:
                alt_seq = vo.state.sequence.root

            # Optionally allow using the length of the reference sequence
            # instead of the sequence itself.
            ref_seq_limit = kwargs.get("ref_seq_limit", 0)
            if ref_seq_limit is not None and len(ref_seq) > int(ref_seq_limit):
                ref_seq = len(ref_seq)

            spdi_expr = f"{alias}:{start}:{ref_seq}:{alt_seq}"
            spdi_exprs.append(spdi_expr)

        return spdi_exprs

    def _post_process_imported_allele(
        self, allele: models.Allele, **kwargs
    ) -> models.Allele:
        """Provide common post-processing for imported Alleles IN-PLACE.

        :param allele: VRS Allele object

        kwargs:
            rle_seq_limit Optional(int): If RLE is set as the new state after
                normalization, this sets the limit for the length of the `sequence`.
                To exclude `sequence` from the response, set to 0.
                For no limit, set to `None`.
            do_normalize (bool): `True` if fully justified normalization should be
                performed. `False` otherwise. Defaults to `True`
        """
        if kwargs.get("do_normalize", True):
            allele = normalize(
                allele,
                self.data_proxy,
                rle_seq_limit=kwargs.get("rle_seq_limit", self.rle_seq_limit),
            )

        if self.identify:
            allele.id = ga4gh_identify(allele)
            allele.location.id = ga4gh_identify(allele.location)

        return allele


class CnvTranslator(_Translator):
    """Class for translating formats from format to VRS Copy Number"""

    def __init__(
        self,
        data_proxy: _DataProxy,
        default_assembly_name: str = "GRCh38",
        identify: bool = True,
    ):
        """Initialize CnvTranslator class"""
        super().__init__(data_proxy, default_assembly_name, identify)
        self.from_translators = {
            "pgxseg": self._from_pgxseg
        }

    def _from_pgxseg(
        self, pgxseg: str, **kwargs
    ) -> models.CopyNumberChange | None:
        """Parse pgxseg into a VRS CNV Object

        https://docs.progenetix.org/file-formats/

        kwargs:
            copy_change: Copy change. If not provided, default is EFO:0030067 for
                deletions and EFO:0030070 for duplications
        """

        m = self.pgxseg_re.match(pgxseg)
        if not m:
            return None
        g = m.groupdict()

        reference_name = g.get("reference_name", "___unknown___")
        if not ":" in reference_name:
            reference_name = f"{self.default_assembly_name}:{reference_name}"
        refget_accession = self.data_proxy.derive_refget_accession(reference_name)
        if not refget_accession:
            return None

        start = int(g.get("start", 0))
        end = int(g.get("end", start + 1))
        location = models.SequenceLocation(
            sequenceReference=models.SequenceReference(
                refgetAccession=refget_accession
            ),
            start=start,
            end=end,
        )

        copy_change = kwargs.get("copy_change", g.get("variant_state_label", "__unknown__"))
        cnv = models.CopyNumberChange(
            location=location,
            copyChange=copy_change,
        )

        return self._post_process_imported_cnv(cnv)

    def _post_process_imported_cnv(
        self, copy_number: models.CopyNumberChange | models.CopyNumberCount
    ) -> models.CopyNumberChange | models.CopyNumberCount:
        """Provide common post-processing for imported Copy Numbers IN-PLACE."""
        if self.identify:
            copy_number.id = ga4gh_identify(copy_number)
            copy_number.location.id = ga4gh_identify(copy_number.location)

        return copy_number


class AdjacencyTranslator(_Translator):
    """Class for translating formats from format to VRS Adjacency"""

    def __init__(
        self,
        data_proxy: _DataProxy,
        default_assembly_name: str = "GRCh38",
        identify: bool = True,
    ):
        """Initialize AdjacencyTranslator class"""
        super().__init__(data_proxy, default_assembly_name, identify)
        self.from_translators = {
            "pgxadjoined": self._from_pgxadjoined
        }

    def _from_pgxadjoined(
        self, pgxadjoined: str, **kwargs
    ) -> models.Adjacency | None:
        """

        """

        m = self.pgxadjoined_re.match(pgxadjoined)
        if not m:
            return None
        g = m.groupdict()

        adjoined_sequences = []
        for ri in ["1", "2"]:
            refseq = g.get(f"adj_seqid_{ri}", "___unknown___")
            refget_accession = self.data_proxy.derive_refget_accession(refseq)
            if not refget_accession:
                return None
            range_l = list(int(x) for x in re.split(",", g.get(f"range_{ri}", [])))
            pos_type = g.get(f"pos_type_{ri}", "end")
            adjoined_sequences.append(
                models.SequenceLocation(
                    sequenceReference=models.SequenceReference(
                        refgetAccession=refget_accession
                    ),
                    **{pos_type: range_l}
                )
            )

        adjacency = models.Adjacency(
            adjoinedSequences=adjoined_sequences
        )

        return self._post_process_imported_adjacency(adjacency)

    def _post_process_imported_adjacency(
        self, adjacency: models.Adjacency
    ) -> models.Adjacency:
        """Provide common post-processing for imported Copy Numbers IN-PLACE."""
        if self.identify:
            adjacency.id = ga4gh_identify(adjacency)

        return adjacency
