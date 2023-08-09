from typing import Optional, Union, Dict, List
from rdflib.plugins.shared.jsonld.context import source_to_json, Context as JSONLD_Context


class Context(JSONLD_Context):
    """Context class will hold a JSON-LD context in two forms: iri and document.

    See also: https://w3c.github.io/json-ld-syntax/#the-context
    Taken from nexusforge.commons.context
    """

    def __init__(self, document: Union[Dict, List, str], iri: Optional[str] = None) -> None:
        """Initialize the Context and resolves the document if necessary.

        The document can be provided as a dictionary, list or string. If a dictionary or list is
        provided, we assume that nothing needs to be resolved. If a string is provided,
        it should correspond to a resolvable document (i.e. file://, http://) which will be
        resolved in the initialization, the result will become the document and the iri will
        be the initial document parameter. Will throw an exception if the context is not resolvable.

        Arguments
        ----------
            document : dict, list, str
                Resolved or resolvable document
            iri : str
                The iri for the provided document
        """
        super().__init__(document)
        if isinstance(document, list):
            sub_docs = dict()
            for x in document:
                sub_context = Context(x)
                sub_docs.update(sub_context.document["@context"])
            self.document = {"@context": sub_docs}
        elif isinstance(document, str):
            try:
                self.document = source_to_json(document)
            except Exception:
                raise ValueError("context not resolvable")
        elif isinstance(document, Dict):
            self.document = document if "@context" in document else {"@context": document}
        self.iri = iri
        self.prefixes = {v: k for k, v in self._prefixes.items() if k.endswith(("/", "#"))}

    def is_http_iri(self):
        if self.iri:
            return self.iri.startswith("http")
        else:
            return False

    def has_vocab(self):
        return self.vocab is not None


def get_project_context(project_data):
    """Get the context from a project.
    
    Arguments
    ---------
    project_data : dict
        The information contained in the project payload.
    
    Returns
    -------
    context: Context
        An instance of the Context class, an extension of the JSON-LD Context from
        rdflib. Contains the JSON-LD framed context in `context.document`, as well
        as the `context.vocab` and `context.base` attributes.
    """
    context = {"@base": project_data["base"], "@vocab": project_data["vocab"]}
    for mapping in project_data['apiMappings']:
        context[mapping['prefix']] = mapping['namespace']
    return Context(context)