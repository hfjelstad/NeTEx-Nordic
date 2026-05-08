# LLM Agent Entry Point

This folder contains resources for LLM agents working with the Nordic NeTEx Profile.

## For agents

1. Start with `Tables/TableOfContent.md` to understand what's documented
2. Use `ontology/netex-nordic.ttl` for structural queries (element order, types, cardinality)
3. Use `scripts/validate.py` to validate any XML you produce
4. Follow templates in `Templates/` when creating new documentation

## Key conventions

- **One profile**: Nordic NeTEx only
- **Validation**: Always validate against `XSD/xsd/NeTEx_publication.xsd` (full constraints)
- **Element order**: Consult the TTL ontology — XSD sequences are strict
- **IDs**: Follow pattern `<Codespace>:<ObjectType>:<LocalId>`
- **Examples**: Must be complete `PublicationDelivery` documents that validate
