# Topic

Works in OpenAlex are tagged with Topics using an automated system that takes into account the available information about the work, including title, abstract, source (journal) name, and citations.

Topics are grouped into subfields, which are grouped into fields, which are grouped into top-level domains. Each topic has one subfield, one field, and one domain, so each of these may also be used to classify the work, depending on the level of granularity you want.

!!! info
    For further details about `Topics` objects, consult the OpenAlex [documentation](https://docs.openalex.org/api-entities/concepts){target=_blank}.

::: pub_analyzer.models.topic
    options:
        show_source: false
        inherited_members: true
        members_order: source
        members:
            - Topic
            - DehydratedTopic
            - TopicIDs
            - TopicLevel
